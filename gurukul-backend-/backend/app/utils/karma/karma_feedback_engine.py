"""
Karmic Feedback Engine

Computes net karmic influence and publishes it as telemetry.
"""
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import requests
from app.core.karma_database import karma_events_col, users_col
from app.core.karma_config import TOKEN_ATTRIBUTES
from app.utils.karma.karma_engine import compute_karma
from app.utils.karma.event_bus import publish_karma_feedback
from app.utils.karma.sovereign_bridge import emit_karma_signal, SignalType
import asyncio

# Setup logging
logger = logging.getLogger(__name__)

class KarmicFeedbackEngine:
    """Computes net karmic influence and publishes telemetry"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the feedback engine"""
        self.config = config or {}
        self.stp_bridge_url = self.config.get("stp_bridge_url", "http://localhost:8001/insightflow")
        self.feedback_batch_size = self.config.get("feedback_batch_size", 10)
        self.feedback_interval = self.config.get("feedback_interval", 60)  # seconds
        
        # Constraint mode: operate as silent governor instead of active decision engine
        try:
            from .sovereign_bridge import is_constraint_only_mode
            self.constraint_only_mode = is_constraint_only_mode()
        except ImportError:
            self.constraint_only_mode = self.config.get("constraint_only_mode", False)
        
    def compute_dynamic_influence(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute dynamic influence = reward_score – penalty_score ± behavioral bias
        
        Args:
            user_doc: User document from database
            
        Returns:
            Dict with influence metrics
        """
        # Calculate net karma using existing karma engine
        # Extract interaction log from user document to compute karma
        interaction_log = user_doc.get("interaction_log", [])
        karma_calc = compute_karma(interaction_log)
        
        # Extract reward and penalty scores
        balances = user_doc.get("balances", {})
        
        # Calculate reward score (positive karma)
        reward_score = 0
        for token in ["DharmaPoints", "SevaPoints", "PunyaTokens"]:
            reward_score += balances.get(token, 0)
        
        # Calculate penalty score (negative karma)
        penalty_score = 0
        if "PaapTokens" in balances:
            paap_tokens = balances["PaapTokens"]
            for severity in paap_tokens:
                if severity in TOKEN_ATTRIBUTES["PaapTokens"]:
                    multiplier = TOKEN_ATTRIBUTES["PaapTokens"][severity]["multiplier"]
                    penalty_score += paap_tokens[severity] * multiplier
        
        # Calculate behavioral bias (based on recent activity patterns)
        behavioral_bias = self._calculate_behavioral_bias(user_doc)
        
        # Compute dynamic influence
        dynamic_influence = reward_score - penalty_score + behavioral_bias
        
        # In constraint mode, only compute and return influence without taking action
        # This makes the system operate as a silent governor rather than active decision engine
        
        return {
            "user_id": user_doc.get("user_id"),
            "reward_score": reward_score,
            "penalty_score": penalty_score,
            "behavioral_bias": behavioral_bias,
            "dynamic_influence": dynamic_influence,
            "net_karma": karma_calc.get("net_karma", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_behavioral_bias(self, user_doc: Dict[str, Any]) -> float:
        """
        Calculate behavioral bias based on recent activity patterns
        
        Args:
            user_doc: User document from database
            
        Returns:
            float: Behavioral bias value
        """
        user_id = user_doc.get("user_id")
        if not user_id:
            return 0.0
            
        # Get recent karma events for this user
        recent_events = list(karma_events_col.find(
            {"data.user_id": user_id}
        ).sort("timestamp", -1).limit(20))
        
        if not recent_events:
            return 0.0
            
        # Calculate pattern-based bias
        positive_actions = 0
        negative_actions = 0
        
        for event in recent_events:
            event_type = event.get("event_type", "")
            data = event.get("data", {})
            
            # Count positive vs negative actions
            if event_type == "life_event":
                action = data.get("action", "")
                if action in ["completing_lessons", "helping_peers", "solving_doubts", "selfless_service"]:
                    positive_actions += 1
                elif action == "cheat":
                    negative_actions += 1
        
        # Calculate bias based on action ratio
        total_actions = positive_actions + negative_actions
        if total_actions == 0:
            return 0.0
            
        positive_ratio = positive_actions / total_actions
        bias = (positive_ratio - 0.5) * 10  # Scale the bias
        
        return bias
    
    def aggregate_per_user_and_module(self, user_id: str) -> Dict[str, Any]:
        """
        Aggregate karmic influence per user and per module
        
        Args:
            user_id: User ID to aggregate for
            
        Returns:
            Dict with aggregated metrics
        """
        # Get user document
        user_doc = users_col.find_one({"user_id": user_id})
        if not user_doc:
            raise ValueError(f"User {user_id} not found")
        
        # Compute dynamic influence
        influence = self.compute_dynamic_influence(user_doc)
        
        # Get module-specific events
        module_events = list(karma_events_col.find(
            {"data.user_id": user_id, "source": {"$exists": True}}
        ))
        
        # Aggregate by module
        module_influence = {}
        for event in module_events:
            source = event.get("source", "unknown")
            if source not in module_influence:
                module_influence[source] = {
                    "event_count": 0,
                    "total_influence": 0,
                    "last_event_timestamp": event.get("timestamp")
                }
            module_influence[source]["event_count"] += 1
            module_influence[source]["total_influence"] += influence["dynamic_influence"]
            if event.get("timestamp") > module_influence[source]["last_event_timestamp"]:
                module_influence[source]["last_event_timestamp"] = event.get("timestamp")
        
        return {
            "user_id": user_id,
            "overall_influence": influence,
            "module_influence": module_influence,
            "aggregation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def publish_feedback_signal(self, user_id: str, 
                                    insightflow_endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Publish feedback signal to InsightFlow bridge
        
        Args:
            user_id: User ID to publish signal for
            insightflow_endpoint: Override endpoint URL
            
        Returns:
            Dict with publication result
        """
        try:
            # Aggregate data
            aggregated_data = self.aggregate_per_user_and_module(user_id)
            
            # In constraint-only mode, just compute and return without publishing
            if self.constraint_only_mode:
                return {
                    "status": "computed_only",
                    "user_id": user_id,
                    "influence_data": aggregated_data,
                    "constraint_mode": True,
                    "message": "Signal computed but not published - operating in constraint-only mode"
                }
            
            # Prepare signal payload
            signal_payload = {
                "signal_id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": "karmic_influence",
                "data": aggregated_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Emit signal to Sovereign Core for authorization
            event_metadata = {
                "source": "karmic_feedback_engine",
                "user_id": user_id,
                "signal_id": signal_payload["signal_id"]
            }
            
            # First, emit to Sovereign Core for authorization
            sovereign_result = emit_karma_signal(SignalType.FEEDBACK_SIGNAL, {
                "payload": signal_payload,
                "event_metadata": event_metadata
            })
            
            # Only proceed with actual transmission if authorized
            if sovereign_result.get("authorized", False):
                # Publish to event bus
                publish_karma_feedback(signal_payload, event_metadata)
                
                # Send to STP bridge
                endpoint = insightflow_endpoint or self.stp_bridge_url
                result = self._send_to_stp_bridge(signal_payload, endpoint)
                
                # Log transmission
                self._log_transmission(signal_payload, result)
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "signal_id": signal_payload["signal_id"],
                    "sent_to": endpoint,
                    "result": result,
                    "authorized": True
                }
            else:
                logger.info(f"Signal {signal_payload['signal_id']} rejected by Sovereign Core")
                return {
                    "status": "rejected",
                    "user_id": user_id,
                    "signal_id": signal_payload["signal_id"],
                    "authorized": False,
                    "authorization_reason": sovereign_result.get("authorization_response", {}).get("reason", "Not authorized by Sovereign Core")
                }
            
        except Exception as e:
            logger.error(f"Error publishing feedback signal for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "user_id": user_id,
                "error": str(e)
            }
    
    def _send_to_stp_bridge(self, payload: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """
        Send payload to STP bridge module
        
        Args:
            payload: Signal payload to send
            endpoint: Endpoint URL
            
        Returns:
            Dict with response details
        """
        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            response_data = response.json() if response.content else {}
            return {
                "status_code": response.status_code,
                "response": response_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error sending to STP bridge: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _log_transmission(self, payload: Dict[str, Any], result: Dict[str, Any]):
        """
        Log transmission in audit.log with hash + timestamp
        
        Args:
            payload: Transmitted payload
            result: Transmission result
        """
        try:
            # Create hash of payload
            payload_str = json.dumps(payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
            
            # Log to audit
            audit_entry = {
                "transmission_id": str(uuid.uuid4()),
                "payload_hash": payload_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload_summary": {
                    "signal_id": payload.get("signal_id"),
                    "user_id": payload.get("user_id"),
                    "type": payload.get("type")
                },
                "result": result
            }
            
            # Log to file
            with open("logs/audit.log", "a") as f:
                f.write(f"{json.dumps(audit_entry)}\n")
                
        except Exception as e:
            logger.error(f"Error logging transmission: {str(e)}")
    
    async def batch_publish_feedback_signals(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Publish feedback signals for multiple users in batch
        
        Args:
            user_ids: List of user IDs to publish signals for
            
        Returns:
            List of results for each user
        """
        results = []
        for user_id in user_ids:
            result = await self.publish_feedback_signal(user_id)
            results.append(result)
            
            # Add small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)
            
        return results

# Global instance
feedback_engine = KarmicFeedbackEngine()

# Alias for backward compatibility
KarmaFeedbackEngine = KarmicFeedbackEngine

# Convenience functions
def compute_user_influence(user_id: str) -> Dict[str, Any]:
    """Compute karmic influence for a user"""
    user_doc = users_col.find_one({"user_id": user_id})
    if not user_doc:
        raise ValueError(f"User {user_id} not found")
    return feedback_engine.compute_dynamic_influence(user_doc)

async def publish_user_feedback_signal(user_id: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
    """Publish feedback signal for a user"""
    return await feedback_engine.publish_feedback_signal(user_id, endpoint)

async def batch_publish_feedback_signals(user_ids: List[str]) -> List[Dict[str, Any]]:
    """Publish feedback signals for multiple users"""
    return await feedback_engine.batch_publish_feedback_signals(user_ids)