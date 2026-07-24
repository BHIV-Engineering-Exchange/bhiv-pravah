# app/telemetry_bus/models.py
"""
Telemetry Bus Data Models

Defines packet structures for telemetry streaming.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DecisionPayload(BaseModel):
    """Decision information in telemetry packet"""
    selected_agent: str = Field(..., description="ID of selected agent")
    alternatives: List[str] = Field(
        default_factory=list,
        description="List of alternative agents considered"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    latency_ms: float = Field(..., ge=0.0, description="Decision latency in ms")
    strategy: str = Field(default="weighted_scoring", description="Routing strategy")


class FeedbackPayload(BaseModel):
    """Feedback information in telemetry packet"""
    reward_signal: Optional[float] = Field(None, ge=-1.0, le=1.0)
    last_outcome: Optional[str] = Field(None, description="success|failure|pending")


class TracePayload(BaseModel):
    """Trace metadata in telemetry packet"""
    version: str = Field(default="v3", description="InsightFlow version")
    node: str = Field(default="insightflow-router", description="Node identifier")
    ts: str = Field(..., description="ISO timestamp")


class STPPayload(BaseModel):
    """STP enrichment fields (Phase C)"""
    karmic_weight: Optional[float] = Field(None, ge=-1.0, le=1.0)
    context_tags: List[str] = Field(default_factory=list)
    version: str = Field(default="stp-1")


class TelemetryPacket(BaseModel):
    """
    Complete telemetry packet structure.
    
    Example:
    {
      "request_id": "r-9f1a",
      "decision": {...},
      "feedback": {...},
      "trace": {...},
      "stp": {...}  # Optional, added in Phase C
    }
    """
    request_id: str = Field(..., description="Unique request identifier")
    decision: DecisionPayload
    feedback: FeedbackPayload = Field(default_factory=FeedbackPayload)
    trace: TracePayload
    stp: Optional[STPPayload] = None  # Added in Phase C
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "r-9f1a",
                "decision": {
                    "selected_agent": "nlp_processor",
                    "alternatives": ["tts_generator", "vision_analyzer"],
                    "confidence": 0.87,
                    "latency_ms": 142,
                    "strategy": "q_learning"
                },
                "feedback": {
                    "reward_signal": 0.12,
                    "last_outcome": "success"
                },
                "trace": {
                    "version": "v3",
                    "node": "insightflow-router",
                    "ts": "2025-11-15T11:15:00Z"
                }
            }
        }


class PolicyUpdatePayload(BaseModel):
    """
    Policy update information for closed-loop learning.
    
    Emitted after each feedback event to show real-time adaptation.
    """
    previous_confidence: float = Field(..., ge=0.0, le=1.0)
    new_confidence: float = Field(..., ge=0.0, le=1.0)
    delta_q_value: float = Field(..., description="Change in Q-value")
    karma_delta: Optional[float] = Field(None, description="Karma contribution")
    routing_strategy_change: Optional[str] = Field(
        None,
        description="Strategy change if any"
    )


class PolicyUpdatePacket(BaseModel):
    """
    Policy update telemetry packet.
    
    Sent after feedback to show routing adaptation.
    """
    request_id: str = Field(..., description="Original request ID")
    agent_id: str = Field(..., description="Agent that was updated")
    policy_update: PolicyUpdatePayload
    trace: TracePayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "r-9f1a",
                "agent_id": "nlp-001",
                "policy_update": {
                    "previous_confidence": 0.87,
                    "new_confidence": 0.91,
                    "delta_q_value": 0.04,
                    "karma_delta": 0.02,
                    "routing_strategy_change": None
                },
                "trace": {
                    "version": "v3.1",
                    "node": "insightflow-router",
                    "ts": "2025-11-21T11:30:00Z"
                }
            }
        }


class HealthResponse(BaseModel):
    """Telemetry health check response"""
    status: str = Field(default="ok")
    queue_size: int = Field(..., ge=0, description="Current queue size")
    max_queue_size: int = Field(..., description="Maximum queue capacity")
    active_connections: int = Field(..., ge=0)
    messages_sent: int = Field(..., ge=0)
    messages_dropped: int = Field(default=0, ge=0)
    uptime_seconds: float = Field(..., ge=0.0)


# Legacy compatibility models
class LegacyDecisionPayload(BaseModel):
    """Legacy decision payload for backward compatibility"""
    agent_id: str
    confidence_score: float
    routing_strategy: str
    execution_time_ms: float
    context: Dict[str, Any] = {}


class LegacyTelemetryPacket(BaseModel):
    """Legacy telemetry packet for backward compatibility"""
    event_type: str
    timestamp: datetime
    payload: LegacyDecisionPayload
    session_id: Optional[str] = None