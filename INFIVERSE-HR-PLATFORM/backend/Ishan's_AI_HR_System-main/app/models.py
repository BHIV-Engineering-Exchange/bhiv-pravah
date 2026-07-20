from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import re

class CandidateCreate(BaseModel):
    name: str
    email: str
    phone: str
    skills: List[str]
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.strip().lower()
    
    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+91-\d{10}$', v):
            raise ValueError('Phone must be in format +91-XXXXXXXXXX')
        return v
    
    @validator('skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one skill is required')
        return [skill.strip() for skill in v if skill.strip()]

class FeedbackCreate(BaseModel):
    candidate_id: int
    feedback_score: int
    comment: str
    actual_outcome: str
    
    @validator('candidate_id')
    def validate_candidate_id(cls, v):
        if v <= 0:
            raise ValueError('Candidate ID must be positive')
        return v
    
    @validator('feedback_score')
    def validate_feedback_score(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Feedback score must be between 1 and 5')
        return v
    
    @validator('comment')
    def validate_comment(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment cannot be empty')
        return v.strip()
    
    @validator('actual_outcome')
    def validate_outcome(cls, v):
        allowed_outcomes = ["accept", "reject", "reconsider"]
        if v not in allowed_outcomes:
            raise ValueError(f'Outcome must be one of: {", ".join(allowed_outcomes)}')
        return v

class AutomationTrigger(BaseModel):
    candidate_id: int
    event_type: str
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('candidate_id')
    def validate_candidate_id(cls, v):
        if v <= 0:
            raise ValueError('Candidate ID must be positive')
        return v
    
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_events = ["shortlisted", "rejected", "interview_scheduled", "onboarding_completed"]
        if v not in allowed_events:
            raise ValueError(f'Event type must be one of: {", ".join(allowed_events)}')
        return v