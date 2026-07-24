# Feedback schemas
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


class FeedbackResponse(BaseModel):
    """Feedback response schema"""
    id: str
    routing_log_id: str
    agent_id: str
    feedback_type: FeedbackType
    success: bool
    latency_ms: float
    accuracy_score: Optional[float] = None
    user_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    error_details: Optional[str] = Field(None, max_length=500)
    metadata: Dict = {}
    created_at: Optional[str] = None