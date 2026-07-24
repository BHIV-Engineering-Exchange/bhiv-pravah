"""
Karma Integration for Bucket
Forwards behavioral events from Core to Karma Chain for tracking
"""
import aiohttp
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KarmaForwarder:
    """Forwards events from Bucket to Karma Chain"""
    
    def __init__(self, karma_url: str = "http://localhost:8000", timeout: float = 2.0):
        self.karma_url = karma_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.enabled = True
        
    async def forward_agent_event(
        self,
        event_data: Dict[str, Any],
        user_id: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Forward agent execution event to Karma"""
        if not self.enabled:
            return None
            
        try:
            # Extract relevant data
            agent_id = event_data.get("agent_id", "unknown")
            task_id = event_data.get("task_id", "unknown")
            event_type = event_data.get("event_type", "agent_execution")
            
            # Determine action based on event type
            if event_type == "agent_result":
                result = event_data.get("result", {})
                success = result.get("status") == 200
                action = "agent_success" if success else "agent_failure"
            elif event_type == "rl_outcome":
                reward = event_data.get("reward", 0)
                action = "agent_success" if reward > 0 else "agent_failure"
            else:
                action = "agent_execution"
            
            # Create life event for Karma
            karma_event = {
                "type": "life_event",
                "data": {
                    "user_id": user_id,
                    "action": action,
                    "role": "user",
                    "note": f"Agent {agent_id} execution",
                    "context": json.dumps({
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "event_type": event_type,
                        "source": "bhiv_bucket"
                    }),
                    "metadata": event_data.get("metadata", {})
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "bhiv_bucket"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.karma_url}/v1/event/",
                    json=karma_event
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Karma event forwarded: {agent_id}")
                        return result
                    else:
                        text = await response.text()
                        logger.warning(f"Karma returned {response.status}: {text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.debug("Karma timeout - continuing")
            return None
        except Exception as e:
            logger.debug(f"Karma forward error: {e}")
            return None
    
    async def forward_rl_outcome(
        self,
        agent_id: str,
        reward: float,
        metadata: Dict[str, Any],
        user_id: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Forward RL outcome to Karma as behavioral data"""
        if not self.enabled:
            return None
            
        try:
            action = "learning_success" if reward > 0 else "learning_adjustment"
            
            karma_event = {
                "type": "life_event",
                "data": {
                    "user_id": user_id,
                    "action": action,
                    "role": "user",
                    "note": f"RL outcome for {agent_id}",
                    "context": json.dumps({
                        "agent_id": agent_id,
                        "reward": reward,
                        "source": "bhiv_bucket_rl"
                    }),
                    "metadata": metadata
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "bhiv_bucket"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.karma_url}/v1/event/",
                    json=karma_event
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            logger.debug(f"Karma RL forward error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if Karma service is available"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.karma_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def forward_prana_event(
        self,
        prana_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Forward PRANA telemetry to Karma for behavioral analysis"""
        if not self.enabled:
            return None
            
        try:
            # Map cognitive state to karma action
            state_to_action = {
                "DEEP_FOCUS": "deep_focus_learning",
                "ON_TASK": "active_engagement",
                "THINKING": "contemplative_learning",
                "IDLE": "passive_state",
                "DISTRACTED": "attention_drift",
                "AWAY": "disengagement",
                "OFF_TASK": "task_avoidance"
            }
            
            cognitive_state = prana_data.get("metadata", {}).get("cognitive_state", "ON_TASK")
            action = state_to_action.get(cognitive_state, "user_activity")
            
            karma_event = {
                "type": "life_event",
                "data": {
                    "user_id": prana_data.get("user_id", "unknown"),
                    "action": action,
                    "role": prana_data.get("role", "user"),
                    "note": prana_data.get("note", "PRANA telemetry"),
                    "context": json.dumps({
                        "source": "prana_telemetry",
                        "cognitive_state": cognitive_state,
                        "focus_score": prana_data.get("metadata", {}).get("focus_score", 0),
                        "system_type": prana_data.get("metadata", {}).get("system_type", "unknown"),
                        "session_id": prana_data.get("metadata", {}).get("session_id"),
                        "lesson_id": prana_data.get("metadata", {}).get("lesson_id"),
                        "task_id": prana_data.get("metadata", {}).get("task_id")
                    }),
                    "metadata": prana_data.get("metadata", {})
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "prana_bucket"
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.karma_url}/v1/event/",
                    json=karma_event
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"PRANA event forwarded to Karma: {cognitive_state}")
                        return result
                    else:
                        text = await response.text()
                        logger.warning(f"Karma PRANA forward returned {response.status}: {text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.debug("Karma PRANA timeout - continuing")
            return None
        except Exception as e:
            logger.debug(f"Karma PRANA forward error: {e}")
            return None
    
    def disable(self):
        """Disable Karma forwarding"""
        self.enabled = False
        logger.info("Karma forwarding disabled")
    
    def enable(self):
        """Enable Karma forwarding"""
        self.enabled = True
        logger.info("Karma forwarding enabled")

# Global instance
karma_forwarder = KarmaForwarder()
