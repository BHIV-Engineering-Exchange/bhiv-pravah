from pydantic import BaseModel, Field
from typing import Dict, Optional


class RouteRequest(BaseModel):
    """Request schema for routing"""
    input_data: Dict
    input_type: str = Field(..., pattern=r'^(text|audio|image|video|custom)$', description="Input type: text, audio, image, video, custom")
    context: Optional[Dict] = None
    strategy: str = Field(
        default="q_learning",
        pattern=r'^(rule_based|semantic|q_learning|performance_based)$',
        description="Routing strategy: rule_based, semantic, q_learning, performance_based"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_data": {"text": "What is the weather today?"},
                "input_type": "text",
                "context": {"user_id": "user_123"},
                "strategy": "q_learning"
            }
        }


class RouteResponse(BaseModel):
    """Response schema for routing"""
    request_id: str
    routing_log_id: str
    agent_id: str
    agent_name: str
    agent_type: str
    confidence_score: float
    routing_reason: str
    routing_strategy: str


class FeedbackRequest(BaseModel):
    """Request schema for feedback submission"""
    routing_log_id: str
    success: bool
    latency_ms: float
    accuracy_score: Optional[float] = None
    user_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    response_data: Optional[Dict] = None
    metadata: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "routing_log_id": "log_123",
                "success": True,
                "latency_ms": 145.5,
                "accuracy_score": 0.88,
                "user_satisfaction": 4
            }
        }