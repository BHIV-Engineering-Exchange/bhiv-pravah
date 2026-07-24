"""
BHIV Core → Bucket Integration Client
Non-invasive, fire-and-forget communication to Bucket
Core continues normally even if Bucket is offline
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from utils.logger import get_logger
from integration.insight_client import insight_client

logger = get_logger(__name__)

class BucketClient:
    """Fire-and-forget client for Core → Bucket communication"""
    
    def __init__(self, bucket_url: str = "http://localhost:8001"):
        self.bucket_url = bucket_url.rstrip('/')
        self.session = None
        self.enabled = True
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=2.0)  # 2 second timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def write_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Fire-and-forget write to Bucket with Insight Core validation
        Returns True if sent, False if failed (Core doesn't care)
        """
        if not self.enabled:
            return False
            
        try:
            # Optional: Validate through Insight Core
            validation = await insight_client.validate_request(event_data)
            if not validation.get("validated"):
                logger.debug(f"Insight validation failed: {validation.get('decision', {}).get('reason')}")
            
            session = await self._get_session()
            
            # Add Core metadata
            payload = {
                "requester_id": "bhiv_core",
                "event_data": event_data
            }
            
            # Fire and forget - don't wait for response
            asyncio.create_task(self._send_async(session, "/core/write-event", payload))
            return True
            
        except Exception as e:
            logger.debug(f"Bucket write failed (continuing normally): {e}")
            return False
    
    async def write_rl_outcome(self, agent_id: str, reward: float, metadata: Dict = None) -> bool:
        """Write RL outcome to Bucket"""
        event_data = {
            "event_type": "rl_outcome",
            "agent_id": agent_id,
            "reward": reward,
            "metadata": metadata or {}
        }
        return await self.write_event(event_data)
    
    async def write_agent_result(self, task_id: str, agent_id: str, result: Dict) -> bool:
        """Write agent execution result to Bucket"""
        event_data = {
            "event_type": "agent_result",
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result
        }
        return await self.write_event(event_data)
    
    async def read_context(self, agent_id: str) -> Optional[Dict]:
        """
        Optional read from Bucket with timeout
        Returns None if failed - Core continues normally
        """
        if not self.enabled:
            return None
            
        try:
            session = await self._get_session()
            
            async with session.get(
                f"{self.bucket_url}/core/read-context",
                params={"agent_id": agent_id, "requester_id": "bhiv_core"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("context")
                return None
                
        except Exception as e:
            logger.debug(f"Bucket read failed (continuing normally): {e}")
            return None
    
    async def _send_async(self, session: aiohttp.ClientSession, endpoint: str, payload: Dict):
        """Internal async sender - fire and forget"""
        try:
            async with session.post(
                f"{self.bucket_url}{endpoint}",
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
bucket_client = BucketClient()