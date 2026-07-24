"""
UAO → Karma Integration Client
Fire-and-forget pattern with 2s timeout
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class KarmaClient:
    def __init__(self, karma_url: str = "http://localhost:8000", timeout: int = 2):
        self.karma_url = karma_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def log_orchestration_behavior(
        self,
        action_id: str,
        action_type: str,
        state: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Log UAO orchestration behavior to Karma (fire-and-forget)"""
        try:
            event_data = {
                "type": "life_event",
                "data": {
                    "user_id": metadata.get("user_id", "system"),
                    "action": f"orchestration_{state}",
                    "role": "orchestrator",
                    "note": f"Action {action_id} [{action_type}] transitioned to {state}"
                },
                "source": "unified_action_orchestrator"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.karma_url}/v1/event/",
                    json=event_data
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"UAO behavior logged to Karma: {action_id} [{state}]")
                        return True
                    else:
                        logger.warning(f"Karma returned {response.status} for action {action_id}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.debug(f"Karma timeout (non-blocking) for action {action_id}")
            return False
        except Exception as e:
            logger.debug(f"Karma logging failed (non-blocking): {e}")
            return False

karma_client = KarmaClient()
