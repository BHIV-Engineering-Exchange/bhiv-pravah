"""
Sovereign Bridge Module

Implements the boundary between karma computation and consequence authorization.
KarmaChain emits signals, but Sovereign Core authorizes consequences.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import requests
from fastapi import HTTPException

# Setup logging
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Types of karmic signals that can be emitted"""
    KARMA_COMPUTATION = "karma.computation"
    ATONEMENT_NEEDED = "atonement.needed"
    DEATH_THRESHOLD_REACHED = "death.threshold.reached"
    LIFECYCLE_EVENT = "lifecycle.event"
    FEEDBACK_SIGNAL = "feedback.signal"
    CANONICAL_KARMA_SIGNAL = "karma.signal.canonical"
    CONSTRAINT_ONLY_MODE = "constraint.only.mode"
    ALLOW_ACTION = "action.allow"
    NUDGE_ACTION = "action.nudge"
    RESTRICT_ACTION = "action.restrict"
    ESCALATE_ACTION = "action.escalate"

class SovereignBridge:
    """Bridge between KarmaChain and Sovereign Core authority"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the sovereign bridge"""
        self.config = config or {}
        self.sovereign_core_endpoint = self.config.get(
            "sovereign_core_endpoint", 
            "http://localhost:8002/api/v1/core/authorize"
        )
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.timeout = self.config.get("timeout", 10)
        self.enabled = self.config.get("enabled", True)
        
        # Authority validation
        self.authority_required = self.config.get("authority_required", True)
        
        # Constraint-only mode: operate as silent governor instead of active decision engine
        # By default, this is True as per requirement
        self.constraint_only_mode = self.config.get("constraint_only_mode", True)
        
        # Session for connection reuse
        self.session = requests.Session()
    
    def emit_signal(self, signal_type: SignalType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Emit a karmic signal to Sovereign Core for authorization.
        
        Args:
            signal_type: Type of signal being emitted
            payload: Signal payload containing computation results
            
        Returns:
            Dict with authorization result
        """
        if not self.enabled:
            return {
                "status": "skipped",
                "message": "Sovereign bridge is disabled",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        signal_id = str(uuid.uuid4())
        
        # Prepare the signal for Sovereign Core
        signal_payload = {
            "signal_id": signal_id,
            "signal_type": signal_type.value,
            "source": "karmachain",
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "authorization_status": "pending"
        }
        
        try:
            if self.authority_required:
                # Send to Sovereign Core for authorization
                response = self._request_authorization(signal_payload)
                
                # Return the authorization result
                return {
                    "status": "authorized" if response.get("authorized", False) else "rejected",
                    "signal_id": signal_id,
                    "authorized": response.get("authorized", False),
                    "authorization_response": response,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                # For testing/development - bypass authority
                logger.warning("Authority bypassed - this should not happen in production")
                return {
                    "status": "authorized",
                    "signal_id": signal_id,
                    "authorized": True,
                    "authorization_response": {"reason": "Authority bypassed for testing"},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            error_msg = f"Error emitting signal {signal_id} to Sovereign Core: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "error",
                "signal_id": signal_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _request_authorization(self, signal_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request authorization from Sovereign Core for a karmic signal.
        
        Args:
            signal_payload: The signal requiring authorization
            
        Returns:
            Dict with authorization decision
        """
        last_exception = Exception("Unknown error")
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.post(
                    self.sovereign_core_endpoint,
                    json=signal_payload,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201]:
                    response_data = response.json() if response.content else {}
                    return response_data
                else:
                    logger.warning(
                        f"Authorization attempt {attempt + 1} failed with status {response.status_code}"
                    )
                    last_exception = HTTPException(
                        status_code=response.status_code,
                        detail=f"Sovereign Core returned status {response.status_code}"
                    )
                    
            except Exception as e:
                logger.warning(f"Authorization attempt {attempt + 1} failed with exception: {str(e)}")
                last_exception = e
        
        # If all attempts failed
        raise last_exception
    
    def batch_emit_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Emit multiple signals in batch.
        
        Args:
            signals: List of signals to emit
            
        Returns:
            List of authorization results
        """
        results = []
        
        for signal in signals:
            signal_type = SignalType(signal["signal_type"])
            payload = signal["payload"]
            result = self.emit_signal(signal_type, payload)
            results.append(result)
            
        return results
    
    def is_core_available(self) -> bool:
        """
        Check if the Sovereign Core is available
        
        Returns:
            bool: True if Core is available, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.sovereign_core_endpoint}/health",
                timeout=self.timeout
            )
            return response.status_code in [200, 201]
        except Exception:
            return False
    
    def send_signal(self, signal: 'KarmaSignal') -> Dict[str, Any]:
        """
        Send a karma signal to the Sovereign Core for authorization
        
        Args:
            signal: The karma signal to send
            
        Returns:
            Dict with authorization result
        """
        # In safe mode when Core is offline, return appropriate response
        if not self.is_core_available():
            return {
                "status": "SAFE_MODE",
                "authorized": True,  # Allow in safe mode
                "reason": "Core unavailable, operating in safe mode",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Convert KarmaSignal to appropriate format for Sovereign Core
        signal_data = signal.to_dict()
        
        signal_type = SignalType.CANONICAL_KARMA_SIGNAL
        payload = {
            "karma_signal": signal_data,
            "event_type": "canonical_karma_signal"
        }
        
        return self.emit_signal(signal_type, payload)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the sovereign bridge connection.
        
        Returns:
            Dict with health status
        """
        try:
            # Send a simple health check to the Sovereign Core
            health_payload = {
                "signal_id": str(uuid.uuid4()),
                "signal_type": SignalType.FEEDBACK_SIGNAL.value,
                "source": "karmachain",
                "payload": {"type": "health_check"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response = self.session.post(
                f"{self.sovereign_core_endpoint}/health",
                json=health_payload,
                timeout=self.timeout
            )
            
            status = "healthy" if response.status_code in [200, 201] else "unhealthy"
            
            return {
                "status": status,
                "endpoint": self.sovereign_core_endpoint,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": self.sovereign_core_endpoint,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

# Global instance
sovereign_bridge = SovereignBridge()

# Convenience functions
def emit_karma_signal(signal_type: SignalType, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Emit a karmic signal to Sovereign Core"""
    return sovereign_bridge.emit_signal(signal_type, payload)

def batch_emit_karma_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Emit multiple karmic signals to Sovereign Core"""
    return sovereign_bridge.batch_emit_signals(signals)

def check_sovereign_bridge_health() -> Dict[str, Any]:
    """Check the health of the sovereign bridge"""
    return sovereign_bridge.health_check()


def is_constraint_only_mode() -> bool:
    """Check if the system is in constraint-only mode"""
    return sovereign_bridge.constraint_only_mode
