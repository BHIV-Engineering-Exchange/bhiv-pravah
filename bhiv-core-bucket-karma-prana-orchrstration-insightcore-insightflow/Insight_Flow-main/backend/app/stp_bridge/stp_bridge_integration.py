# app/stp_bridge/stp_bridge_integration.py
"""
STP Bridge Integration

Lightweight adapter for wrapping decisions in STP format and parsing
STP feedback from behavioral service.

Naming: stpLayer, semanticTokenProtocol, semanticTokenTranslator, stpMiddleware
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class STPDecisionWrapper(BaseModel):
    """STP-wrapped decision packet"""
    stp_version: str = Field(default="stp-1", description="STP protocol version")
    stp_token: str = Field(..., description="Unique STP token")
    stp_timestamp: str = Field(..., description="ISO timestamp")
    stp_type: str = Field(default="decision_packet", description="Packet type")
    stp_metadata: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(..., description="Original decision data")


class STPFeedbackInput(BaseModel):
    """STP feedback from behavioral service"""
    karmic_weight: Optional[float] = Field(None, ge=-1.0, le=1.0)
    reward_value: Optional[float] = Field(None, ge=-1.0, le=1.0)
    context_tags: List[str] = Field(default_factory=list)
    stp_version: str = Field(default="stp-1")


class STPFeedbackOutput(BaseModel):
    """Parsed STP feedback for routing"""
    reward: float = Field(..., description="Normalized reward signal")
    weights: Dict[str, float] = Field(default_factory=dict)
    context_tags: List[str] = Field(default_factory=list)


class STPBridgeIntegration:
    """
    STP Bridge Integration layer.
    
    Provides functions to:
    1. wrap_decision_for_stp(decision_packet) -> dict
    2. parse_stp_feedback(payload) -> {reward, weights}
    
    Treats tokenized feedback as numeric/context metadata only.
    No semantic interpretation.
    """
    
    STP_VERSION = "stp-1"
    
    def __init__(self, enable_feedback: bool = False):
        """
        Initialize STP bridge.
        
        Args:
            enable_feedback: Toggle for STP feedback enrichment
        """
        self.enable_feedback = enable_feedback
        
        logger.info(
            f"STPBridgeIntegration initialized (feedback_enabled={enable_feedback})"
        )
    
    def wrap_decision_for_stp(
        self,
        decision_packet: Dict[str, Any],
        stp_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Wrap decision packet in STP format.
        
        Args:
            decision_packet: Original decision data
            stp_token: Optional pre-generated STP token
            metadata: Optional additional metadata
        
        Returns:
            STP-wrapped decision packet
        """
        try:
            # Generate token if not provided
            if stp_token is None:
                stp_token = self._generate_stp_token()
            
            # Create STP wrapper
            wrapped = STPDecisionWrapper(
                stp_token=stp_token,
                stp_timestamp=datetime.utcnow().isoformat() + "Z",
                stp_metadata=metadata or {},
                payload=decision_packet
            )
            
            logger.debug(f"Wrapped decision in STP: {stp_token}")
            
            return wrapped.model_dump()
        
        except Exception as e:
            logger.error(f"Error wrapping decision for STP: {str(e)}")
            # Return unwrapped on error
            return decision_packet
    
    def parse_stp_feedback(
        self,
        payload: Dict[str, Any]
    ) -> STPFeedbackOutput:
        """
        Parse STP feedback from behavioral service.
        
        Args:
            payload: Raw STP feedback payload
        
        Returns:
            Parsed feedback with reward and weights
        
        Note:
            Treats fields as numeric/contextual inputs only.
            No semantic interpretation of tags or weights.
        """
        try:
            # Parse input
            feedback_input = STPFeedbackInput(**payload)
            
            # Extract reward (prioritize reward_value, fallback to karmic_weight)
            reward = feedback_input.reward_value
            if reward is None:
                reward = feedback_input.karmic_weight or 0.0
            
            # Extract weights (treat as generic numeric modifiers)
            weights = {
                "karmic_weight": feedback_input.karmic_weight or 0.0,
                "reward_value": feedback_input.reward_value or 0.0,
            }
            
            # Parse context tags (treat as metadata strings)
            context_tags = feedback_input.context_tags
            
            output = STPFeedbackOutput(
                reward=reward,
                weights=weights,
                context_tags=context_tags
            )
            
            logger.debug(
                f"Parsed STP feedback: reward={reward:.2f}, "
                f"tags={len(context_tags)}"
            )
            
            return output
        
        except Exception as e:
            logger.error(f"Error parsing STP feedback: {str(e)}")
            # Return neutral feedback on error
            return STPFeedbackOutput(
                reward=0.0,
                weights={},
                context_tags=[]
            )
    
    def enrich_telemetry_packet(
        self,
        telemetry_packet: Dict[str, Any],
        stp_feedback: Optional[STPFeedbackOutput] = None
    ) -> Dict[str, Any]:
        """
        Enrich telemetry packet with STP fields.
        
        Args:
            telemetry_packet: Original telemetry packet
            stp_feedback: Optional parsed STP feedback
        
        Returns:
            Enriched telemetry packet with STP section
        """
        if not self.enable_feedback or stp_feedback is None:
            return telemetry_packet
        
        try:
            # Add STP enrichment section
            telemetry_packet["stp"] = {
                "karmic_weight": stp_feedback.weights.get("karmic_weight"),
                "context_tags": stp_feedback.context_tags,
                "version": self.STP_VERSION
            }
            
            logger.debug("Enriched telemetry packet with STP fields")
            
            return telemetry_packet
        
        except Exception as e:
            logger.error(f"Error enriching telemetry: {str(e)}")
            return telemetry_packet
    
    @staticmethod
    def _generate_stp_token() -> str:
        """Generate unique STP token"""
        import hashlib
        import time
        
        timestamp = str(time.time_ns())
        hash_val = hashlib.sha256(timestamp.encode()).hexdigest()[:12]
        return f"stp-{hash_val}"


# Global STP bridge instance
_stp_bridge: Optional[STPBridgeIntegration] = None


def get_stp_bridge(enable_feedback: bool = False) -> STPBridgeIntegration:
    """
    Get or create global STP bridge instance.
    
    Args:
        enable_feedback: Enable STP feedback enrichment
    
    Returns:
        STPBridgeIntegration instance
    """
    global _stp_bridge
    
    if _stp_bridge is None:
        _stp_bridge = STPBridgeIntegration(enable_feedback=enable_feedback)
    
    return _stp_bridge