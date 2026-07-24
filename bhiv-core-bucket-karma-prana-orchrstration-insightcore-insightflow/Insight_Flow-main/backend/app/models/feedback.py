from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """Feedback type enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    USER_RATING = "user_rating"


class Feedback(BaseModel):
    """Feedback event database model"""
    id: Optional[str] = None
    routing_log_id: str
    agent_id: str
    feedback_type: FeedbackType
    success: bool
    latency_ms: float = Field(ge=0.0)
    accuracy_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    user_satisfaction: Optional[int] = Field(default=None, ge=1, le=5)
    error_details: Optional[str] = Field(None, max_length=500)
    metadata: Dict = {}
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "routing_log_id": "log_123",
                "agent_id": "agent_nlp_001",
                "feedback_type": "success",
                "success": True,
                "latency_ms": 145.5,
                "accuracy_score": 0.88,
                "user_satisfaction": 4
            }
        }


class PerformanceMetrics(BaseModel):
    """Aggregated performance metrics model"""
    id: Optional[str] = None
    agent_id: str
    time_window: str  # hourly, daily, weekly
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency_ms: float = 0.0
    average_accuracy: float = 0.0
    average_confidence: float = 0.0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None