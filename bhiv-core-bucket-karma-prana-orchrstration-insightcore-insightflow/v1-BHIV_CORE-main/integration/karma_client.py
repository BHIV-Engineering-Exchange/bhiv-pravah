"""
Karma Client - Direct integration between BHIV Core and Karma Chain
Enables behavioral tracking and karma computation for agent actions
"""
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KarmaClient:
    def __init__(self, karma_url: str = "http://localhost:8000", timeout: float = 2.0):
        self.karma_url = karma_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
    async def log_life_event(
        self,
        user_id: str,
        action: str,
        role: str,
        note: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Log a life event (user action) to Karma"""
        try:
            event_data = {
                "type": "life_event",
                "data": {
                    "user_id": user_id,
                    "action": action,
                    "role": role,
                    "note": note,
                    "context": context or {},
                    "metadata": metadata or {}
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "bhiv_core"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.karma_url}/v1/event/",
                    json=event_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Karma life event logged: {user_id} - {action}")
                        return result
                    else:
                        logger.warning(f"Karma returned {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.debug("Karma timeout - continuing")
            return None
        except Exception as e:
            logger.debug(f"Karma error: {e}")
            return None
    
    async def log_agent_execution(
        self,
        agent_id: str,
        task_id: str,
        user_id: str,
        success: bool,
        processing_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Log agent execution as a life event"""
        action = "agent_success" if success else "agent_failure"
        
        context = {
            "agent_id": agent_id,
            "task_id": task_id,
            "processing_time": processing_time,
            "success": success
        }
        
        return await self.log_life_event(
            user_id=user_id,
            action=action,
            role="user",
            note=f"Agent {agent_id} execution",
            context=context,
            metadata=metadata
        )
    
    async def get_user_karma(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user karma profile"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.karma_url}/api/v1/karma/{user_id}"
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception:
            return None
    
    async def health_check(self) -> bool:
        """Check if Karma service is available"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.karma_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
