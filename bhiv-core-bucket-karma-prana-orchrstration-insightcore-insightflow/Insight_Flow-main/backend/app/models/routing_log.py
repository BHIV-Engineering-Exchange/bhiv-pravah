from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RoutingStatus(str, Enum):
    """Routing status enumeration"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class RoutingLog(BaseModel):
    """Routing log database model"""
    id: Optional[str] = None
    request_id: str
    user_id: Optional[str] = None
    input_type: str  # text, audio, image, etc.
    input_data: Dict[str, Any]
    selected_agent_id: str
    agent_name: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    routing_reason: str
    routing_strategy: str  # rule_based, semantic, llm_based, q_learning
    status: RoutingStatus = RoutingStatus.PENDING
    execution_time_ms: Optional[float] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    context: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_123456",
                "user_id": "user_789",
                "input_type": "text",
                "input_data": {"text": "What is the weather today?"},
                "selected_agent_id": "agent_nlp_001",
                "agent_name": "NLP Processor",
                "confidence_score": 0.92,
                "routing_reason": "High semantic match for weather query",
                "routing_strategy": "semantic"
            }
        }