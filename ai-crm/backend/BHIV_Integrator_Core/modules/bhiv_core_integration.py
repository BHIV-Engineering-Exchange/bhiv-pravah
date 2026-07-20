"""
BHIV Core Integration Module
Handles connection to BHIV Core agent registry and decision engine
"""

import requests
from typing import Dict, Any, Optional
from config.settings import settings
from unified_logging.logger import UnifiedLogger

class BHIVCoreIntegration:
    def __init__(self):
        self.base_url = settings.get("bhiv_core_url", "http://localhost:8002")
        self.api_key = settings.get("bhiv_core_api_key", "uniguru-dev-key-2025")
        self.logger = UnifiedLogger()

    async def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent with BHIV Core registry"""
        try:
            payload = {
                "agent_config": agent_config,
                "system": "bhiv_integrator",
                "api_key": self.api_key
            }

            response = requests.post(
                f"{self.base_url}/agent/register",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                await self.logger.log_event({
                    "event_type": "agent_registered",
                    "source_system": "bhiv_integrator",
                    "payload": {"agent_id": agent_config.get("id"), "registration_result": result},
                    "status": "success"
                })
                return result
            else:
                return {
                    "error": f"Registration failed: {response.status_code}",
                    "status_code": response.status_code
                }

        except Exception as e:
            await self.logger.log_event({
                "event_type": "agent_registration_failed",
                "source_system": "bhiv_integrator",
                "payload": {"agent_id": agent_config.get("id"), "error": str(e)},
                "status": "error"
            })
            return {"error": f"Registration error: {str(e)}"}

    async def make_decision(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Request decision from BHIV Core agent"""
        try:
            payload = {
                "query": query,
                "context": context,
                "system": "bhiv_integrator",
                "api_key": self.api_key
            }

            response = requests.post(
                f"{self.base_url}/agent/decide",
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                await self.logger.log_event({
                    "event_type": "bhiv_decision_made",
                    "source_system": "bhiv_integrator",
                    "payload": {"query": query[:100], "decision": result.get("decision")},
                    "status": "success"
                })
                return result
            else:
                return {
                    "error": f"Decision failed: {response.status_code}",
                    "fallback": self._fallback_decision(query, context)
                }

        except Exception as e:
            await self.logger.log_event({
                "event_type": "bhiv_decision_failed",
                "source_system": "bhiv_integrator",
                "payload": {"query": query[:100], "error": str(e)},
                "status": "error"
            })
            return {
                "error": f"Decision error: {str(e)}",
                "fallback": self._fallback_decision(query, context)
            }

    def _fallback_decision(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback decision when BHIV Core is unavailable"""
        # Simple rule-based fallback
        query_lower = query.lower()

        if "order" in query_lower or "procurement" in query_lower:
            return {
                "decision": "route_to_logistics",
                "agent": "logistics_agent",
                "confidence": 0.7,
                "fallback": True
            }
        elif "lead" in query_lower or "opportunity" in query_lower or "account" in query_lower:
            return {
                "decision": "route_to_crm",
                "agent": "crm_agent",
                "confidence": 0.8,
                "fallback": True
            }
        elif "task" in query_lower or "review" in query_lower or "feedback" in query_lower:
            return {
                "decision": "route_to_task_manager",
                "agent": "task_agent",
                "confidence": 0.6,
                "fallback": True
            }
        else:
            return {
                "decision": "route_to_uniguru",
                "agent": "knowledge_agent",
                "confidence": 0.5,
                "fallback": True
            }

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get BHIV Core agent registry status"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unavailable", "error": response.status_code}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def sync_agents(self, local_agents: Dict[str, Any]) -> Dict[str, Any]:
        """Sync local agents with BHIV Core registry"""
        results = {"registered": [], "failed": []}

        for agent_id, agent_config in local_agents.items():
            result = await self.register_agent(agent_config)
            if "error" not in result:
                results["registered"].append(agent_id)
            else:
                results["failed"].append({"agent_id": agent_id, "error": result["error"]})

        await self.logger.log_event({
            "event_type": "agent_sync_completed",
            "source_system": "bhiv_integrator",
            "payload": results,
            "status": "completed"
        })

        return results

    async def query_uniguru(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query UniGuru knowledge system"""
        try:
            payload = {
                "query": query,
                "context": context or {},
                "system": "bhiv_integrator",
                "api_key": self.api_key
            }

            response = requests.post(
                f"{settings['uniguru_url']}/query",
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"UniGuru query failed: {response.status_code}"}

        except Exception as e:
            return {"error": f"UniGuru query error: {str(e)}"}

    async def query_gurukul(self, query: str, pipeline: str = "default") -> Dict[str, Any]:
        """Query Gurukul pipeline system"""
        try:
            payload = {
                "query": query,
                "pipeline": pipeline,
                "system": "bhiv_integrator",
                "api_key": self.api_key
            }

            response = requests.post(
                f"{settings['gurukul_url']}/process",
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Gurukul query failed: {response.status_code}"}

        except Exception as e:
            return {"error": f"Gurukul query error: {str(e)}"}

# Global instance
bhiv_core_integration = BHIVCoreIntegration()