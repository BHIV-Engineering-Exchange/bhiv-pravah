"""
Workflow Executor → Karma Integration Client
Fire-and-forget behavioral tracking for workflow executions
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class KarmaClient:
    """Fire-and-forget client for Workflow → Karma communication"""
    
    def __init__(self, karma_url: str = "http://localhost:8000"):
        self.karma_url = karma_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=5.0)  # Increased from 2.0 to 5.0
        self.enabled = True
        
    async def log_workflow_behavior(
        self,
        trace_id: str,
        user_id: str,
        action_type: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Fire-and-forget behavioral logging
        Returns True if sent, False if failed
        """
        if not self.enabled:
            return False
            
        try:
            # Map workflow status to karma action
            action = f"workflow_{status}" if status in ["success", "failed"] else "workflow_execution"
            
            karma_event = {
                "type": "life_event",
                "data": {
                    "user_id": user_id,
                    "action": action,
                    "role": "user",
                    "note": f"Workflow execution: {action_type}",
                    "context": {
                        "trace_id": trace_id,
                        "action_type": action_type,
                        "status": status,
                        "source": "workflow_executor",
                        **(metadata or {})
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "workflow_executor"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Fire and forget
                asyncio.create_task(self._send_async(session, "/v1/event/", karma_event))
                logger.debug(f"Workflow behavior logged to Karma: {trace_id}")
                return True
                
        except Exception as e:
            logger.debug(f"Karma logging failed (non-blocking): {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Karma is available"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.karma_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _send_async(self, session: aiohttp.ClientSession, endpoint: str, payload: Dict):
        """Internal async sender - fire and forget"""
        try:
            async with session.post(
                f"{self.karma_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                pass  # Don't wait for response
        except Exception:
            pass  # Silently fail

# Global instance
karma_client = KarmaClient()
