"""
BHIV Core → Workflow Executor Integration Client
Fire-and-forget communication for workflow execution
Core continues normally even if Workflow Executor is offline
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from utils.logger import get_logger

logger = get_logger(__name__)

class WorkflowClient:
    """Fire-and-forget client for Core → Workflow Executor communication"""
    
    def __init__(self, workflow_url: str = "http://localhost:8003"):
        self.workflow_url = workflow_url.rstrip('/')
        self.session = None
        self.enabled = True
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=2.0)  # 2 second timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def execute_workflow(
        self,
        trace_id: str,
        action_type: str,
        payload: Dict[str, Any],
        user_id: str = "system"
    ) -> bool:
        """
        Fire-and-forget workflow execution request
        Returns True if sent, False if failed (Core doesn't care)
        """
        if not self.enabled:
            return False
            
        try:
            session = await self._get_session()
            
            # Build workflow request
            request_data = {
                "trace_id": trace_id,
                "decision": "workflow",
                "data": {
                    "workflow_type": "workflow",
                    "payload": {
                        "action_type": action_type,
                        "user_id": user_id,
                        "trace_id": trace_id,
                        **payload
                    }
                }
            }
            
            # Fire and forget - don't wait for response
            asyncio.create_task(self._send_async(session, "/api/workflow/execute", request_data))
            logger.debug(f"Workflow execution request sent: {trace_id} - {action_type}")
            return True
            
        except Exception as e:
            logger.debug(f"Workflow execution failed (continuing normally): {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Workflow Executor is available"""
        if not self.enabled:
            return False
            
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.workflow_url}/healthz") as response:
                return response.status == 200
                
        except Exception as e:
            logger.debug(f"Workflow Executor health check failed: {e}")
            return False
    
    async def _send_async(self, session: aiohttp.ClientSession, endpoint: str, payload: Dict):
        """Internal async sender - fire and forget"""
        try:
            async with session.post(
                f"{self.workflow_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                # Don't wait for or process response
                pass
        except Exception:
            # Silently fail - Core doesn't care
            pass
    
    async def close(self):
        """Clean up session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
workflow_client = WorkflowClient()
