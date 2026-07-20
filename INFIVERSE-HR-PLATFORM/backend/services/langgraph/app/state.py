from typing import TypedDict, Annotated, Sequence, Literal, Optional
from langchain_core.messages import BaseMessage
import operator

class CandidateApplicationState(TypedDict):
    """State for candidate application processing workflow"""
    # Identifiers
    candidate_id: int
    job_id: int
    application_id: int
    
    # Candidate data
    candidate_email: str
    candidate_phone: str
    candidate_name: str
    
    # Job data
    job_title: str
    job_description: str
    
    # Status
    application_status: Literal["pending", "shortlisted", "rejected", "interview_scheduled", "offered", "onboarded"]
    
    # Messages
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Tracking
    notifications_sent: list[dict]
    matching_score: float
    ai_recommendation: str
    
    # Sentiment
    sentiment: Literal["positive", "neutral", "negative"]
    
    # Workflow
    next_action: str
    workflow_stage: Literal["screening", "notification", "hr_update", "feedback", "completed"]
    
    # Error handling
    error: Optional[str]
    
    # Timestamps and voice paths
    timestamp: str
    voice_input_path: Optional[str]
    voice_response_path: Optional[str]


class NotificationPayload(TypedDict):
    """Structure for notification data"""
    candidate_id: int
    candidate_email: str
    candidate_phone: str
    candidate_name: str
    job_title: str
    application_status: str
    message: str
    channels: list[str]
    timestamp: str