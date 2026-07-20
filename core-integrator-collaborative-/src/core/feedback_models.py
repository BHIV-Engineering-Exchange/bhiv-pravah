from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Dict, Any
from datetime import datetime

class CanonicalFeedbackSchema(BaseModel):
    """Canonical feedback schema used across Gateway, Storage, and Noopur forwarding"""
    generation_id: int = Field(..., gt=0, description="ID of the generation to provide feedback for")
    command: Literal["+2", "+1", "-1", "-2"] = Field(..., description="Feedback command (+2=excellent, +1=good, -1=poor, -2=terrible)")
    user_id: str = Field(..., min_length=1, description="User ID providing feedback")
    comment: Optional[str] = Field(None, max_length=500, description="Optional feedback comment")
    timestamp: Optional[datetime] = Field(None, description="Feedback timestamp (auto-generated if not provided)")
    
    @model_validator(mode='before')
    @classmethod
    def set_timestamp(cls, values):
        if isinstance(values, dict) and 'timestamp' not in values:
            values['timestamp'] = datetime.utcnow()
        return values
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        if v not in ["+2", "+1", "-1", "-2"]:
            raise ValueError(f"Invalid command: {v}. Must be one of: +2, +1, -1, -2")
        return v
    
    def to_storage_format(self) -> Dict[str, Any]:
        """Convert to storage format"""
        return self.dict()
    
    def to_noopur_format(self) -> Dict[str, Any]:
        """Convert to Noopur forwarding format"""
        return {
            "generation_id": self.generation_id,
            "command": self.command,
            "user_id": self.user_id,
            "comment": self.comment
        }

# Alias for backward compatibility
FeedbackRequest = CanonicalFeedbackSchema