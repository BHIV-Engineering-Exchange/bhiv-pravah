"""
Canonical Karma Signal Contract Implementation
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from .sovereign_bridge import SignalType, emit_karma_signal


class KarmaSignal:
    """Canonical Karma Signal according to the specification"""
    
    def __init__(self, subject_id: str, context: Optional[str] = None, signal: str = "nudge", 
                 severity: float = 0.0, reason_code: str = "GENERIC", 
                 ttl: int = 300, requires_core_ack: bool = True, product_context: Optional[str] = None,
                 opaque_reason_code: Optional[str] = None):
        """
        Initialize a canonical karma signal
        
        Args:
            subject_id: UUID of the subject
            context: Platform context (assistant | game | finance | gurukul | infra | workflow)
            signal: Type of signal (allow | nudge | restrict | escalate)
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code for the signal (no human-readable explanations)
            ttl: Time to live in seconds
            requires_core_ack: Whether Core ACK is required before applying consequences
            product_context: Alternative name for context (backward compatibility)
        """
        # Handle backward compatibility - prioritize product_context, then context, then default to 'unknown'
        final_context = product_context if product_context is not None else context if context is not None else "unknown"
        
        # Handle reason code backward compatibility - use opaque_reason_code if provided, otherwise use reason_code
        final_reason_code = opaque_reason_code if opaque_reason_code is not None else reason_code
        
        self.data = {
            "subject_id": subject_id,
            "context": final_context,  # Maintain the context field for backward compatibility
            "product_context": final_context,  # Also store as product_context
            "signal": signal,
            "severity": severity,
            "reason_code": final_reason_code,  # Keep original parameter name for compatibility
            "opaque_reason_code": final_reason_code,  # Also store as opaque_reason_code
            "ttl": ttl,
            "requires_core_ack": requires_core_ack,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": str(uuid.uuid4())
        }
        
        # Store context as an instance attribute for backward compatibility
        self.context = final_context
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the signal as a dictionary"""
        return self.data
    
    @property
    def subject_id(self):
        return self.data.get("subject_id")
    
    @property
    def product_context(self):
        return self.data.get("product_context")
    
    @property
    def signal(self):
        return self.data.get("signal")
    
    @property
    def severity(self):
        return self.data.get("severity")
    
    @property
    def opaque_reason_code(self):
        return self.data.get("opaque_reason_code")
    
    @property
    def ttl(self):
        return self.data.get("ttl", 300)
    
    @property
    def requires_core_ack(self):
        return self.data.get("requires_core_ack", True)
    
    @property
    def timestamp(self):
        return self.data.get("timestamp")
    
    @property
    def signal_id(self):
        return self.data.get("signal_id")
    
    @property
    def reason_code(self):
        return self.data.get("reason_code")
    
    @classmethod
    def create_signal(cls, subject_id: str, context: Optional[str] = None, signal: str = "nudge", 
                      severity: float = 0.0, reason_code: str = "GENERIC",
                      ttl: int = 300, requires_core_ack: bool = True, product_context: Optional[str] = None,
                      opaque_reason_code: Optional[str] = None) -> 'KarmaSignal':
        """
        Create a canonical karma signal according to specification
        
        Args:
            subject_id: UUID of the subject
            context: Platform context (assistant | game | finance | gurukul | infra | workflow)
            signal: Type of signal (allow | nudge | restrict | escalate)
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code for the signal (no human-readable explanations)
            ttl: Time to live in seconds
            requires_core_ack: Whether Core ACK is required before applying consequences
            product_context: Alternative name for context (backward compatibility)
            opaque_reason_code: Alternative name for reason_code (backward compatibility)
            
        Returns:
            KarmaSignal: New canonical karma signal
        """
        return cls(subject_id, context, signal, severity, reason_code, ttl, requires_core_ack, product_context, opaque_reason_code)


def emit_canonical_karma_signal(subject_id: str, context: Optional[str] = None, signal: str = "nudge",
                               severity: float = 0.0, reason_code: str = "GENERIC",
                               ttl: int = 300, requires_core_ack: bool = True,
                               opaque_reason_code: Optional[str] = None, product_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Emit a canonical karma signal to Sovereign Core for authorization
    
    Args:
        subject_id: UUID of the subject
        context: Platform context (assistant | game | finance | gurukul | infra | workflow)
        signal: Type of signal (allow | nudge | restrict | escalate)
        severity: Severity level (0.0 to 1.0)
        reason_code: Opaque reason code for the signal (no human-readable explanations)
        ttl: Time to live in seconds
        requires_core_ack: Whether Core ACK is required before applying consequences
        opaque_reason_code: Alternative name for reason_code (backward compatibility)
        
    Returns:
        Dict: Authorization result from Sovereign Core
    """
    karma_signal = KarmaSignal(subject_id, context, signal, severity, reason_code, ttl, requires_core_ack, product_context, opaque_reason_code)
    
    return emit_karma_signal(
        SignalType.CANONICAL_KARMA_SIGNAL,
        {
            "karma_signal": karma_signal.to_dict(),
            "event_type": "canonical_karma_signal"
        }
    )


def enforce_constraint_only_mode(enabled: bool = True) -> Dict[str, Any]:
    """
    Enable or disable constraint-only mode globally
    
    Args:
        enabled: Whether to enable constraint-only mode
        
    Returns:
        Dict: Status of the operation
    """
    from .sovereign_bridge import sovereign_bridge
    sovereign_bridge.constraint_only_mode = enabled
    
    return {
        "status": "success",
        "constraint_only_mode": enabled,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def is_constraint_only_mode() -> bool:
    """
    Check if constraint-only mode is enabled
    
    Returns:
        bool: Whether constraint-only mode is enabled
    """
    from .sovereign_bridge import sovereign_bridge
    return getattr(sovereign_bridge, 'constraint_only_mode', False)


def evaluate_constraint_signal(user_id: str, action: str, context: str) -> Optional[Dict[str, Any]]:
    """
    Evaluate whether an action requires constraint-based handling
    
    Args:
        user_id: ID of the user performing the action
        action: The action being performed
        context: Context where the action occurs
        
    Returns:
        Optional[Dict]: Signal if constraint is needed, None otherwise
    """
    # This is a simplified evaluation - in a real system, this would be more complex
    constraint_signals = {
        "cheat": {"signal": "restrict", "severity": 0.8, "opaque_reason_code": "CHEAT_DETECTED"},
        "harassment": {"signal": "restrict", "severity": 0.9, "opaque_reason_code": "HARASSMENT_DETECTED"},
        "spam": {"signal": "nudge", "severity": 0.6, "opaque_reason_code": "SPAM_DETECTED"},
        "rudeness": {"signal": "nudge", "severity": 0.4, "opaque_reason_code": "RUDE_BEHAVIOR_DETECTED"},
        "unsafe_intent": {"signal": "restrict", "severity": 0.95, "opaque_reason_code": "UNSAFE_INTENT_DETECTED"},
        "ignoring_guidance": {"signal": "nudge", "severity": 0.3, "opaque_reason_code": "GUIDANCE_IGNORED"},
        "politeness": {"signal": "allow", "severity": 0.2, "opaque_reason_code": "POSITIVE_BEHAVIOR"},
        "thoughtful_question": {"signal": "allow", "severity": 0.1, "opaque_reason_code": "ENGAGEMENT_POSITIVE"},
        "acknowledging_guidance": {"signal": "allow", "severity": 0.1, "opaque_reason_code": "POSITIVE_FEEDBACK"}
    }
    
    if action in constraint_signals:
        signal_info = constraint_signals[action]
        return {
            "subject_id": user_id,
            "context": context,
            "product_context": context,
            "signal": signal_info["signal"],
            "severity": signal_info["severity"],
            "reason_code": signal_info["opaque_reason_code"],  # For backward compatibility
            "opaque_reason_code": signal_info["opaque_reason_code"],
            "ttl": 300,
            "requires_core_ack": True
        }
    
    return None