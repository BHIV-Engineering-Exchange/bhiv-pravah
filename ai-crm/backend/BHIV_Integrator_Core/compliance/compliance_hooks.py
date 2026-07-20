"""
Compliance Hooks for BHIV Integrator Core
Integrates Sankalp compliance checks across all transactions
"""

import requests
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from config.settings import settings

class ComplianceHooks:
    def __init__(self):
        self.sankalp_url = settings.get("sankalp_compliance_url", "http://localhost:8007")
        self.compliance_enabled = settings.get("compliance_enabled", True)

    async def check_transaction_compliance(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance for a transaction using EMS event forwarding"""
        if not self.compliance_enabled:
            return {"compliant": True, "message": "Compliance checks disabled"}

        try:
            # Use EMS forward endpoint to log the transaction for compliance tracking
            ems_payload = {
                "actor": transaction.get("user_id", transaction.get("system", "bhiv_integrator")),
                "action": "transaction_check",
                "resource": f"transaction/{transaction.get('id', transaction.get('transaction_id', 'unknown'))}",
                "status": "pending",
                "reason": "compliance_validation",
                "purpose": "audit_trail",
                "ems_trace_id": transaction.get("trace_id", str(uuid.uuid4())),
                "ems_source": "bhiv_integrator",
                "details": {
                    "transaction_type": transaction.get("type"),
                    "amount": transaction.get("amount", 0),
                    "parties": transaction.get("parties", []),
                    "system": transaction.get("system", "bhiv_integrator"),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": transaction.get("metadata", {})
                }
            }

            response = requests.post(
                f"{self.sankalp_url}/ems-forward",
                json=ems_payload,
                headers={"X-API-Key": "uniguru-dev-key-2025"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Transaction logged for compliance: {transaction.get('id', 'unknown')}")
                # For transactions, we assume compliant if logging succeeds
                return {
                    "compliant": True,
                    "message": "Transaction logged for compliance tracking",
                    "ems_ingested": result.get("ingested", False)
                }
            else:
                print(f"⚠️ Compliance logging failed: {response.status_code}")
                return {
                    "compliant": False,
                    "message": f"Compliance service error: {response.status_code}",
                    "error_code": response.status_code
                }

        except Exception as e:
            print(f"❌ Compliance check error: {str(e)}")
            return {
                "compliant": False,
                "message": f"Compliance service unavailable: {str(e)}",
                "error": str(e)
            }

    async def validate_data_privacy(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Validate data privacy compliance using consent management"""
        if not self.compliance_enabled:
            return {"valid": True, "message": "Privacy checks disabled"}

        try:
            # Check if user has consented to data processing for this data type
            user_id = data.get("user_id", data.get("employee_id", "unknown"))

            # Get user consent
            response = requests.get(
                f"{self.sankalp_url}/consent/{user_id}",
                headers={"X-API-Key": "uniguru-dev-key-2025"},
                timeout=5
            )

            if response.status_code == 200:
                consent_data = response.json()
                data_categories = consent_data.get("data_categories", [])

                # Check if the data type is in allowed categories
                if data_type in data_categories or "all" in data_categories:
                    return {
                        "valid": True,
                        "message": "Data privacy validated via user consent",
                        "consent_verified": True
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"Data type '{data_type}' not in user's consented categories",
                        "consent_verified": False
                    }
            else:
                return {
                    "valid": False,
                    "message": f"Consent check failed: {response.status_code}"
                }

        except Exception as e:
            return {
                "valid": False,
                "message": f"Privacy validation error: {str(e)}"
            }

    async def audit_trail_log(self, action: str, user_id: str, resource: str, details: Dict[str, Any]) -> str:
        """Log audit trail entry using EMS forward"""
        if not self.compliance_enabled:
            return "audit_disabled"

        try:
            # Use EMS forward for audit logging
            ems_payload = {
                "actor": user_id,
                "action": action,
                "resource": resource,
                "status": "success",
                "reason": "audit_trail",
                "purpose": "compliance",
                "ems_trace_id": str(uuid.uuid4()),
                "ems_source": "bhiv_integrator",
                "details": {
                    **details,
                    "timestamp": datetime.now().isoformat(),
                    "system": "bhiv_integrator"
                }
            }

            response = requests.post(
                f"{self.sankalp_url}/ems-forward",
                json=ems_payload,
                headers={"X-API-Key": "uniguru-dev-key-2025"},
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                audit_id = str(uuid.uuid4())  # Generate local audit ID since EMS doesn't return one
                print(f"✅ Audit log forwarded to compliance system: {audit_id}")
                return audit_id
            else:
                print(f"⚠️ Audit log failed: {response.status_code}")
                return "audit_failed"

        except Exception as e:
            print(f"❌ Audit log error: {str(e)}")
            return "audit_error"

    async def check_access_control(self, user_id: str, resource: str, action: str) -> Dict[str, Any]:
        """Check access control permissions using consent and audit logging"""
        if not self.compliance_enabled:
            return {"allowed": True, "message": "Access control disabled"}

        try:
            # Check if user has monitoring consent enabled
            response = requests.get(
                f"{self.sankalp_url}/consent/{user_id}",
                headers={"X-API-Key": "uniguru-dev-key-2025"},
                timeout=5
            )

            if response.status_code == 200:
                consent_data = response.json()
                monitoring_enabled = consent_data.get("monitoring_enabled", False)

                if monitoring_enabled:
                    # Log the access attempt
                    await self.audit_trail_log(
                        action=f"access_{action}",
                        user_id=user_id,
                        resource=resource,
                        details={"action": action, "monitoring_consent": True}
                    )

                    return {
                        "allowed": True,
                        "message": "Access granted with monitoring consent",
                        "consent_verified": True
                    }
                else:
                    return {
                        "allowed": False,
                        "message": "Access denied: monitoring consent not granted",
                        "consent_verified": False
                    }
            else:
                return {
                    "allowed": False,
                    "message": f"Consent check failed: {response.status_code}"
                }

        except Exception as e:
            return {
                "allowed": False,
                "message": f"Access control error: {str(e)}"
            }

    async def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data (local implementation with consent logging)"""
        if not self.compliance_enabled:
            return data

        try:
            # Log encryption activity for compliance
            await self.audit_trail_log(
                action="data_encryption",
                user_id=data.get("user_id", "system"),
                resource="sensitive_data",
                details={"fields_encrypted": list(data.keys()), "encryption_method": "local"}
            )

            # For now, implement simple obfuscation (in production, use proper encryption)
            encrypted_data = {}
            for key, value in data.items():
                if isinstance(value, str) and any(word in key.lower() for word in ["password", "ssn", "credit", "personal"]):
                    # Simple ROT13-like obfuscation for demo (replace with real encryption)
                    encrypted_data[key] = f"ENC:{value[::-1]}"  # Reverse string as simple obfuscation
                else:
                    encrypted_data[key] = value

            return encrypted_data

        except Exception as e:
            print(f"❌ Encryption error: {str(e)}")
            return data

    async def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive data (local implementation)"""
        if not self.compliance_enabled:
            return encrypted_data

        try:
            # Log decryption activity for compliance
            await self.audit_trail_log(
                action="data_decryption",
                user_id=encrypted_data.get("user_id", "system"),
                resource="sensitive_data",
                details={"decryption_method": "local"}
            )

            # Reverse the simple obfuscation
            decrypted_data = {}
            for key, value in encrypted_data.items():
                if isinstance(value, str) and value.startswith("ENC:"):
                    # Reverse the obfuscation
                    decrypted_data[key] = value[4:][::-1]  # Remove "ENC:" and unreverse
                else:
                    decrypted_data[key] = value

            return decrypted_data

        except Exception as e:
            print(f"❌ Decryption error: {str(e)}")
            return encrypted_data

    async def get_compliance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get compliance report using audit logs"""
        if not self.compliance_enabled:
            return {"message": "Compliance reporting disabled"}

        try:
            # Get audit logs for the date range
            audit_payload = {
                "start_date": start_date,
                "end_date": end_date,
                "user_id": None,  # Get all users
                "action": None,   # Get all actions
                "limit": 1000     # Large limit for reporting
            }

            response = requests.post(
                f"{self.sankalp_url}/audit-logs",
                json=audit_payload,
                headers={"X-API-Key": "uniguru-dev-key-2025"},
                timeout=15
            )

            if response.status_code == 200:
                audit_logs = response.json()

                # Generate compliance summary from audit logs
                total_logs = len(audit_logs)
                compliance_actions = [log for log in audit_logs if log.get("action", "").startswith(("compliance", "consent", "audit"))]
                successful_actions = [log for log in audit_logs if log.get("status") == "success"]

                return {
                    "report_period": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "summary": {
                        "total_audit_logs": total_logs,
                        "compliance_related_actions": len(compliance_actions),
                        "successful_actions": len(successful_actions),
                        "compliance_rate": (len(successful_actions) / total_logs * 100) if total_logs > 0 else 0
                    },
                    "logs": audit_logs[:100],  # Return first 100 logs
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "error": f"Audit log retrieval failed: {response.status_code}",
                    "status_code": response.status_code
                }

        except Exception as e:
            return {
                "error": f"Compliance report error: {str(e)}",
                "exception": str(e)
            }

    def update_compliance_flags(self, flags: Dict[str, bool]):
        """Update compliance flags in settings"""
        current_flags = settings.get("compliance_flags", {})
        current_flags.update(flags)
        settings["compliance_flags"] = current_flags
        print(f"🔄 Updated compliance flags: {current_flags}")

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance status"""
        return {
            "enabled": self.compliance_enabled,
            "sankalp_url": self.sankalp_url,
            "flags": settings.get("compliance_flags", {}),
            "last_check": datetime.now().isoformat()
        }