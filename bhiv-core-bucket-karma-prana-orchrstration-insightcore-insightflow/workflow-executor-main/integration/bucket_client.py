"""
Workflow Executor → Bucket Integration Client
Fire-and-forget event logging for workflow executions
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class BucketClient:
    """Fire-and-forget client for Workflow → Bucket communication"""
    
    def __init__(self, bucket_url: str = "http://localhost:8001"):
        self.bucket_url = bucket_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=5.0)  # Increased from 2.0 to 5.0
        self.enabled = True
        
    async def log_workflow_execution(
        self,
        trace_id: str,
        action_type: str,
        status: str,
        execution_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Fire-and-forget workflow execution logging
        Returns True if sent, False if failed
        """
        if not self.enabled:
            logger.warning("Bucket client disabled")
            print("[BUCKET CLIENT] Disabled")
            return False
            
        try:
            event_data = {
                "event_type": "workflow_execution",
                "trace_id": trace_id,
                "action_type": action_type,
                "status": status,
                "execution_result": execution_result,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            payload = {
                "requester_id": "workflow_executor",
                "event_data": event_data
            }
            
            logger.info(f"Sending workflow event to Bucket: trace_id={trace_id}")
            print(f"[BUCKET CLIENT] Sending event to {self.bucket_url}/core/write-event")
            print(f"[BUCKET CLIENT] Payload: {payload}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                try:
                    async with session.post(
                        f"{self.bucket_url}/core/write-event",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        response_text = await response.text()
                        print(f"[BUCKET CLIENT] Response status: {response.status}")
                        print(f"[BUCKET CLIENT] Response body: {response_text}")
                        
                        if response.status == 200:
                            logger.info(f"✅ Workflow event logged to Bucket: {trace_id}")
                            print(f"[BUCKET CLIENT] ✅ SUCCESS")
                            return True
                        else:
                            logger.error(f"❌ Bucket rejected event: status={response.status}, response={response_text}")
                            print(f"[BUCKET CLIENT] ❌ REJECTED: {response.status}")
                            return False
                except aiohttp.ClientError as e:
                    logger.error(f"❌ Bucket connection error: {e}")
                    print(f"[BUCKET CLIENT] ❌ CONNECTION ERROR: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Bucket logging failed: {e}")
            print(f"[BUCKET CLIENT] ❌ EXCEPTION: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    async def health_check(self) -> bool:
        """Check if Bucket is available"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.bucket_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False

# Global instance
bucket_client = BucketClient()
