"""
Unified Logging System for BHIV Integrator Core
Handles structured logging across all modules with DHI scoring and compliance tracking
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from config.settings import settings

class UnifiedLogger:
    def __init__(self):
        self.log_store = []
        self.db_url = settings.get("database_url", "sqlite:///./bhiv_integrator.db")

    async def log_event(self, event_data: Dict[str, Any]) -> str:
        """Log an event with structured data"""
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "system": "bhiv_integrator",
            "event_type": event_data.get("event_type", "unknown"),
            "reference_id": event_data.get("event_id", str(uuid.uuid4())),
            "status": event_data.get("status", "unknown"),
            "timestamp": event_data.get("timestamp", datetime.now().isoformat()),
            "dhi_score": event_data.get("dhi_score", 0.0),
            "compliance_flag": event_data.get("compliance_flag", False),
            "payload": event_data.get("payload", {}),
            "metadata": {
                "source_system": event_data.get("source_system"),
                "target_systems": event_data.get("target_systems", []),
                "correlation_id": event_data.get("correlation_id"),
                "processing_time": event_data.get("processing_time")
            }
        }

        # Store locally
        self.log_store.append(log_entry)

        # Sync to central DB
        await self._sync_to_database(log_entry)

        # Send to BHIV Core if configured
        await self._send_to_bhiv_core(log_entry)

        print(f"📝 Logged event: {log_entry['event_type']} (ID: {log_entry['log_id']})")
        return log_entry["log_id"]

    async def log_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Log a transaction with compliance tracking"""
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "system": transaction_data.get("system", "unknown"),
            "event_type": "transaction",
            "reference_id": transaction_data.get("transaction_id", str(uuid.uuid4())),
            "status": transaction_data.get("status", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "dhi_score": self._calculate_transaction_dhi_score(transaction_data),
            "compliance_flag": await self._check_transaction_compliance(transaction_data),
            "payload": transaction_data,
            "metadata": {
                "transaction_type": transaction_data.get("type"),
                "amount": transaction_data.get("amount"),
                "parties": transaction_data.get("parties", []),
                "compliance_records": transaction_data.get("compliance_records", [])
            }
        }

        # Store and sync
        self.log_store.append(log_entry)
        await self._sync_to_database(log_entry)
        await self._send_to_bhiv_core(log_entry)

        print(f"💰 Logged transaction: {transaction_data.get('type')} (ID: {log_entry['log_id']})")
        return log_entry["log_id"]

    async def log_api_call(self, api_data: Dict[str, Any]) -> str:
        """Log API calls between systems"""
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "system": "api_gateway",
            "event_type": "api_call",
            "reference_id": api_data.get("request_id", str(uuid.uuid4())),
            "status": api_data.get("status_code", 200),
            "timestamp": datetime.now().isoformat(),
            "dhi_score": self._calculate_api_dhi_score(api_data),
            "compliance_flag": api_data.get("compliance_checked", False),
            "payload": {
                "method": api_data.get("method"),
                "endpoint": api_data.get("endpoint"),
                "response_time": api_data.get("response_time")
            },
            "metadata": {
                "source_system": api_data.get("source"),
                "target_system": api_data.get("target"),
                "user_id": api_data.get("user_id")
            }
        }

        # Store and sync
        self.log_store.append(log_entry)
        await self._sync_to_database(log_entry)

        print(f"🔗 Logged API call: {api_data.get('method')} {api_data.get('endpoint')} (Status: {api_data.get('status_code')})")
        return log_entry["log_id"]

    def _calculate_transaction_dhi_score(self, transaction: Dict[str, Any]) -> float:
        """Calculate DHI score for transactions"""
        score = 0.5  # Base score

        # Compliance factor
        if transaction.get("compliance_records"):
            score += 0.2

        # Amount factor (higher amounts get higher scrutiny)
        amount = transaction.get("amount", 0)
        if amount > 10000:
            score += 0.1
        elif amount < 100:
            score -= 0.1

        # Transaction type factor
        tx_type = transaction.get("type", "")
        if tx_type in ["order", "payment"]:
            score += 0.1

        return min(1.0, max(0.0, score))

    async def _check_transaction_compliance(self, transaction: Dict[str, Any]) -> bool:
        """Check compliance for transactions"""
        if not settings.get("compliance_enabled", False):
            return True

        try:
            # Call Sankalp compliance service
            compliance_payload = {
                "transaction_id": transaction.get("transaction_id"),
                "type": transaction.get("type"),
                "amount": transaction.get("amount"),
                "parties": transaction.get("parties", []),
                "system": transaction.get("system")
            }

            response = requests.post(
                f"{settings['sankalp_compliance_url']}/check",
                json=compliance_payload,
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("compliant", False)
            else:
                print(f"⚠️ Compliance check failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Compliance check error: {str(e)}")
            return False

    def _calculate_api_dhi_score(self, api_call: Dict[str, Any]) -> float:
        """Calculate DHI score for API calls"""
        score = 0.3  # Base score for API calls

        # Response time factor
        response_time = api_call.get("response_time", 0)
        if response_time < 1.0:
            score += 0.3
        elif response_time > 5.0:
            score -= 0.2

        # Status code factor
        status = api_call.get("status_code", 500)
        if status < 400:
            score += 0.2
        else:
            score -= 0.3

        # Endpoint sensitivity
        endpoint = api_call.get("endpoint", "")
        if any(word in endpoint.lower() for word in ["payment", "personal", "sensitive"]):
            score += 0.2

        return min(1.0, max(0.0, score))

    async def _sync_to_database(self, log_entry: Dict[str, Any]):
        """Sync log entry to central database"""
        try:
            db_url = self.db_url.lower()

            if "sqlite" in db_url or "postgresql" in db_url or "mysql" in db_url:
                # SQL Database sync
                await self._sync_to_sql_db(log_entry)
            elif "mongodb" in db_url or "mongo" in db_url:
                # MongoDB sync
                await self._sync_to_mongo_db(log_entry)
            else:
                # Default to activity_log table via REST API
                await self._sync_via_api(log_entry)

            print(f"💾 Synced log {log_entry['log_id']} to database")

        except Exception as e:
            print(f"❌ Database sync failed: {str(e)}")

    async def _sync_to_sql_db(self, log_entry: Dict[str, Any]):
        """Sync to SQL database (activity_log table)"""
        try:
            # Use requests to call a database service endpoint
            # In production, this would use SQLAlchemy or similar
            db_payload = {
                "table": "activity_log",
                "operation": "insert",
                "data": log_entry
            }

            # Assuming there's a database service running
            db_service_url = settings.get("database_service_url", "http://localhost:8008")
            response = requests.post(f"{db_service_url}/db/insert", json=db_payload, timeout=5)

            if response.status_code != 200:
                print(f"⚠️ SQL DB sync failed: {response.status_code}")

        except Exception as e:
            print(f"❌ SQL DB sync error: {str(e)}")

    async def _sync_to_mongo_db(self, log_entry: Dict[str, Any]):
        """Sync to MongoDB collection"""
        try:
            mongo_payload = {
                "collection": "activity_logs",
                "operation": "insert",
                "data": log_entry
            }

            # Assuming there's a MongoDB service running
            mongo_service_url = settings.get("mongodb_service_url", "http://localhost:8009")
            response = requests.post(f"{mongo_service_url}/mongo/insert", json=mongo_payload, timeout=5)

            if response.status_code != 200:
                print(f"⚠️ MongoDB sync failed: {response.status_code}")

        except Exception as e:
            print(f"❌ MongoDB sync error: {str(e)}")

    async def _sync_via_api(self, log_entry: Dict[str, Any]):
        """Sync via REST API to central logging service"""
        try:
            api_url = settings.get("central_log_api_url", "http://localhost:8010/logs")
            response = requests.post(api_url, json=log_entry, timeout=5)

            if response.status_code not in [200, 201]:
                print(f"⚠️ API sync failed: {response.status_code}")

        except Exception as e:
            print(f"❌ API sync error: {str(e)}")

    async def _send_to_bhiv_core(self, log_entry: Dict[str, Any]):
        """Send log entry to BHIV Core for analysis"""
        try:
            payload = {
                "log_entry": log_entry,
                "source": "bhiv_integrator",
                "api_key": settings.get("bhiv_core_api_key")
            }

            response = requests.post(
                f"{settings['bhiv_core_url']}/logs/ingest",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                print(f"📤 Sent log to BHIV Core: {log_entry['log_id']}")
            else:
                print(f"⚠️ Failed to send log to BHIV Core: {response.status_code}")

        except Exception as e:
            print(f"❌ BHIV Core sync failed: {str(e)}")

    def get_logs(self, system: str = None, event_type: str = None, limit: int = 100) -> list:
        """Get logs with optional filtering"""
        logs = self.log_store[-limit:]  # Get most recent logs

        if system:
            logs = [log for log in logs if log.get("system") == system]

        if event_type:
            logs = [log for log in logs if log.get("event_type") == event_type]

        return logs

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary"""
        logs = self.log_store
        total_logs = len(logs)
        compliant_logs = len([log for log in logs if log.get("compliance_flag", False)])

        return {
            "total_logs": total_logs,
            "compliant_logs": compliant_logs,
            "compliance_rate": (compliant_logs / total_logs * 100) if total_logs > 0 else 0,
            "average_dhi_score": sum(log.get("dhi_score", 0) for log in logs) / total_logs if total_logs > 0 else 0
        }