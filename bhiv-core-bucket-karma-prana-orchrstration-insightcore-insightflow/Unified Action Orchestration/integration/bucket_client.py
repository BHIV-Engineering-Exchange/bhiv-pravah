"""
UAO → Bucket Integration Client
Fire-and-forget pattern with 2s timeout
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BucketClient:
    def __init__(self, bucket_url: str = "http://localhost:8001", timeout: int = 2):
        self.bucket_url = bucket_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def log_orchestration_event(
        self,
        action_id: str,
        action_type: str,
        state: str,
        payload: Dict[str, Any],
        error: Optional[str] = None
    ) -> bool:
        """Log UAO orchestration event to Bucket (fire-and-forget)"""
        try:
            event_data = {
                "requester_id": "unified_action_orchestrator",
                "event_data": {
                    "event_type": "orchestration",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "action_id": action_id,
                    "action_type": action_type,
                    "state": state,
                    "payload": payload,
                    "error": error
                }
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.bucket_url}/core/write-event",
                    json=event_data
                ) as response:
                    if response.status == 200:
                        logger.info(f"UAO event logged to Bucket: {action_id} [{state}]")
                        return True
                    else:
                        logger.warning(f"Bucket returned {response.status} for action {action_id}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.debug(f"Bucket timeout (non-blocking) for action {action_id}")
            return False
        except Exception as e:
            logger.debug(f"Bucket logging failed (non-blocking): {e}")
            return False

bucket_client = BucketClient()
