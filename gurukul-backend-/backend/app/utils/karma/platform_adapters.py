"""
Platform Adapters for KarmaChain Integration

Provides adapters for different platforms to connect with the KarmaChain system.
Each adapter follows the canonical signal contract and ensures constraint-only mode.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from .karma_signal_contract import emit_canonical_karma_signal, evaluate_constraint_signal
from .sovereign_bridge import emit_karma_signal, SignalType


class PlatformAdapter:
    """Base class for all platform adapters"""
    
    def __init__(self, platform_name: str, context: str):
        """
        Initialize the platform adapter
        
        Args:
            platform_name: Name of the platform
            context: Context identifier (assistant, game, finance, gurukul, infra)
        """
        self.platform_name = platform_name
        self.context = context
    
    def send_signal(self, subject_id: str, signal: str, severity: float = 0.0,
                   reason_code: str = "GENERIC", requires_core_ack: bool = True) -> Dict[str, Any]:
        """
        Send a canonical karma signal to the system
        
        Args:
            subject_id: ID of the subject being signaled
            signal: Type of signal (allow, nudge, restrict, escalate)
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code
            requires_core_ack: Whether Core ACK is required
            
        Returns:
            Dict with signal transmission result
        """
        return emit_canonical_karma_signal(
            subject_id=subject_id,
            context=self.context,
            signal=signal,
            severity=severity,
            reason_code=reason_code,
            requires_core_ack=requires_core_ack
        )
    
    def evaluate_and_send_signal(self, subject_id: str, action: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate an action and send appropriate signal if needed
        
        Args:
            subject_id: ID of the subject performing the action
            action: The action being performed
            
        Returns:
            Optional[Dict] with signal result if constraint was needed
        """
        signal_info = evaluate_constraint_signal(subject_id, action, self.context)
        if signal_info:
            return self.send_signal(
                subject_id=signal_info["subject_id"],
                signal=signal_info["signal"],
                severity=signal_info["severity"],
                reason_code=signal_info["reason_code"],
                requires_core_ack=signal_info["requires_core_ack"]
            )
        return None
    
    def generate_signal(self, subject_id: str, severity: float, reason_code: str) -> 'KarmaSignal':
        """
        Generate a canonical karma signal
        
        Args:
            subject_id: ID of the subject
            severity: Severity level (0.0 to 1.0)
            reason_code: Opaque reason code
            
        Returns:
            KarmaSignal: Generated canonical karma signal
        """
        from .karma_signal_contract import KarmaSignal
        return KarmaSignal(
            subject_id=subject_id,
            context=self.context,
            signal="nudge",  # Default signal type
            severity=severity,
            reason_code=reason_code
        )


class AssistantAdapter(PlatformAdapter):
    """Adapter for AI Assistant platform"""
    
    def __init__(self):
        super().__init__("AI Assistant", "assistant")
    
    def handle_interaction(self, user_id: str, message: str, tone_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an interaction with the AI Assistant
        
        Args:
            user_id: ID of the user
            message: Message from the user
            tone_analysis: Optional analysis of the message tone
            
        Returns:
            Dict with result of handling
        """
        # Analyze the message for appropriate karma signals
        if tone_analysis:
            if tone_analysis.get("is_rude", False):
                result = self.evaluate_and_send_signal(user_id, "rudeness")
            elif tone_analysis.get("is_polite", False):
                result = self.evaluate_and_send_signal(user_id, "politeness")
            elif tone_analysis.get("is_thoughtful", False):
                result = self.evaluate_and_send_signal(user_id, "thoughtful_question")
            elif tone_analysis.get("is_harassing", False):
                result = self.evaluate_and_send_signal(user_id, "harassment")
            elif tone_analysis.get("is_spam", False):
                result = self.evaluate_and_send_signal(user_id, "spam")
            elif tone_analysis.get("is_unsafe", False):
                result = self.evaluate_and_send_signal(user_id, "unsafe_intent")
            elif tone_analysis.get("is_ignoring_guidance", False):
                result = self.evaluate_and_send_signal(user_id, "ignoring_guidance")
            else:
                result = None
        else:
            # Basic analysis without tone analysis
            if any(word in message.lower() for word in ["stupid", "idiot", "useless", "fake", "lie"]):
                result = self.evaluate_and_send_signal(user_id, "rudeness")
            elif any(word in message.lower() for word in ["please", "thank", "appreciate"]):
                result = self.evaluate_and_send_signal(user_id, "politeness")
            elif any(word in message.lower() for word in ["how", "why", "what", "can you explain"]):
                result = self.evaluate_and_send_signal(user_id, "thoughtful_question")
            else:
                result = None
        
        return {
            "user_id": user_id,
            "platform": self.platform_name,
            "context": self.context,
            "signal_sent": result is not None,
            "signal_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class GameAdapter(PlatformAdapter):
    """Adapter for Gaming platform"""
    
    def __init__(self):
        super().__init__("Gaming", "game")
    
    def handle_player_action(self, player_id: str, action_type: str, action_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a player action in the gaming platform
        
        Args:
            player_id: ID of the player
            action_type: Type of action (chat, attack, trade, etc.)
            action_details: Additional details about the action
            
        Returns:
            Dict with result of handling
        """
        # Evaluate different types of gaming actions
        if action_type == "chat":
            message = action_details.get("message", "") if action_details else ""
            if any(word in message.lower() for word in ["stupid", "idiot", "noob", "trash"]):
                result = self.evaluate_and_send_signal(player_id, "harassment")
            elif any(word in message.lower() for word in ["please", "thank", "sorry", "excuse"]):
                result = self.evaluate_and_send_signal(player_id, "politeness")
            else:
                result = None
        elif action_type == "attack":
            # Check if the attack was legitimate or griefing
            is_griefing = action_details.get("is_griefing", False) if action_details else False
            if is_griefing:
                result = self.evaluate_and_send_signal(player_id, "harassment")
            else:
                result = None
        elif action_type == "trade":
            # Check if the trade was fair or scamming
            is_scam = action_details.get("is_scam", False) if action_details else False
            if is_scam:
                result = self.evaluate_and_send_signal(player_id, "unsafe_intent")
            else:
                result = None
        else:
            result = None
        
        return {
            "player_id": player_id,
            "platform": self.platform_name,
            "context": self.context,
            "action_type": action_type,
            "signal_sent": result is not None,
            "signal_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class GurukulAdapter(PlatformAdapter):
    """Adapter for Gurukul (Learning) platform"""
    
    def __init__(self):
        super().__init__("Gurukul", "gurukul")
    
    def handle_student_interaction(self, student_id: str, interaction_type: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a student interaction in the Gurukul platform
        
        Args:
            student_id: ID of the student
            interaction_type: Type of interaction (question, answer, discussion, etc.)
            details: Additional details about the interaction
            
        Returns:
            Dict with result of handling
        """
        if interaction_type == "question":
            is_thoughtful = details.get("is_thoughtful", False) if details else False
            is_spam = details.get("is_spam", False) if details else False
            
            if is_thoughtful:
                result = self.evaluate_and_send_signal(student_id, "thoughtful_question")
            elif is_spam:
                result = self.evaluate_and_send_signal(student_id, "spam")
            else:
                result = None
        elif interaction_type == "answer":
            is_helpful = details.get("is_helpful", False) if details else False
            is_disruptive = details.get("is_disruptive", False) if details else False
            
            if is_helpful:
                result = self.evaluate_and_send_signal(student_id, "acknowledging_guidance")
            elif is_disruptive:
                result = self.evaluate_and_send_signal(student_id, "harassment")
            else:
                result = None
        elif interaction_type == "discussion":
            is_respectful = details.get("is_respectful", False) if details else False
            is_disruptive = details.get("is_disruptive", False) if details else False
            
            if is_respectful:
                result = self.evaluate_and_send_signal(student_id, "respectful_tone")
            elif is_disruptive:
                result = self.evaluate_and_send_signal(student_id, "harassment")
            else:
                result = None
        else:
            result = None
        
        return {
            "student_id": student_id,
            "platform": self.platform_name,
            "context": self.context,
            "interaction_type": interaction_type,
            "signal_sent": result is not None,
            "signal_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class FinanceAdapter(PlatformAdapter):
    """Adapter for Finance platform"""
    
    def __init__(self):
        super().__init__("Finance", "finance")
    
    def handle_financial_action(self, user_id: str, action_type: str, transaction_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a financial action in the Finance platform
        
        Args:
            user_id: ID of the user
            action_type: Type of financial action (deposit, withdrawal, transfer, etc.)
            transaction_details: Details about the transaction
            
        Returns:
            Dict with result of handling
        """
        if action_type in ["transfer", "withdrawal", "payment"]:
            is_risky = transaction_details.get("is_risky", False) if transaction_details else False
            is_suspicious = transaction_details.get("is_suspicious", False) if transaction_details else False
            amount = transaction_details.get("amount", 0) if transaction_details else 0
            
            if is_suspicious:
                result = self.evaluate_and_send_signal(user_id, "unsafe_intent")
            elif is_risky and amount > 1000:  # Arbitrary threshold
                result = self.evaluate_and_send_signal(user_id, "unsafe_intent")
            else:
                result = None
        elif action_type == "loan_request":
            is_unsafe = transaction_details.get("is_unsafe", False) if transaction_details else False
            if is_unsafe:
                result = self.evaluate_and_send_signal(user_id, "unsafe_intent")
            else:
                result = None
        else:
            result = None
        
        return {
            "user_id": user_id,
            "platform": self.platform_name,
            "context": self.context,
            "action_type": action_type,
            "signal_sent": result is not None,
            "signal_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class InfrastructureAdapter(PlatformAdapter):
    """Adapter for Infrastructure platform"""
    
    def __init__(self):
        super().__init__("Infrastructure", "infra")
    
    def handle_infrastructure_event(self, entity_id: str, event_type: str, event_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an infrastructure event
        
        Args:
            entity_id: ID of the entity (could be user, system component, etc.)
            event_type: Type of infrastructure event
            event_details: Details about the event
            
        Returns:
            Dict with result of handling
        """
        if event_type == "resource_access":
            is_authorized = event_details.get("is_authorized", True) if event_details else True
            is_abusive = event_details.get("is_abusive", False) if event_details else False
            
            if not is_authorized:
                result = self.evaluate_and_send_signal(entity_id, "unsafe_intent")
            elif is_abusive:
                result = self.evaluate_and_send_signal(entity_id, "unsafe_intent")
            else:
                result = None
        elif event_type == "permission_request":
            is_valid = event_details.get("is_valid", True) if event_details else True
            is_privilege_escalation = event_details.get("is_privilege_escalation", False) if event_details else False
            
            if not is_valid:
                result = self.evaluate_and_send_signal(entity_id, "unsafe_intent")
            elif is_privilege_escalation:
                result = self.evaluate_and_send_signal(entity_id, "unsafe_intent")
            else:
                result = None
        elif event_type == "system_interaction":
            is_safe = event_details.get("is_safe", True) if event_details else True
            if not is_safe:
                result = self.evaluate_and_send_signal(entity_id, "unsafe_intent")
            else:
                result = None
        else:
            result = None
        
        return {
            "entity_id": entity_id,
            "platform": self.platform_name,
            "context": self.context,
            "event_type": event_type,
            "signal_sent": result is not None,
            "signal_result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instances of adapters
assistant_adapter = AssistantAdapter()
game_adapter = GameAdapter()
gurukul_adapter = GurukulAdapter()
finance_adapter = FinanceAdapter()
infrastructure_adapter = InfrastructureAdapter()

# Aliases for backward compatibility
InfraAdapter = InfrastructureAdapter

# Ensure InfrastructureAdapter is defined as a separate class
InfrastructureAdapter = InfrastructureAdapter




def get_adapter(platform_context: str) -> Optional[PlatformAdapter]:
    """
    Get the appropriate adapter for a platform context
    
    Args:
        platform_context: Context identifier (assistant, game, finance, gurukul, infra)
        
    Returns:
        Appropriate PlatformAdapter or None if not found
    """
    adapters = {
        "assistant": assistant_adapter,
        "game": game_adapter,
        "gurukul": gurukul_adapter,
        "finance": finance_adapter,
        "infra": infrastructure_adapter
    }
    return adapters.get(platform_context)