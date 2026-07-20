from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Literal


class CoreRequest(BaseModel):
    """Request model for the core gateway endpoint"""
    module: Literal["finance", "education", "creator", "sample_text", "video"] = Field(..., description="Target module name")
    intent: Literal["generate", "analyze", "review", "get_status", "list_videos", "feedback", "history"] = Field(..., description="Intent for the module to perform")
    user_id: str = Field(..., min_length=1)
    data: Dict[str, Any] = Field(default_factory=dict)


class CoreResponse(BaseModel):
    """Response model for the core gateway endpoint"""
    status: Literal["success", "error"] = Field(..., description="Overall status")
    message: str = Field(..., description="Human-readable message")
    result: Any = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def ensure_fields(cls, values):
        if isinstance(values, dict):
            values.setdefault("status", "success")
            values.setdefault("message", "")
            values.setdefault("result", {})
        return values