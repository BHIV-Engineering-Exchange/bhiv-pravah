from pydantic import BaseModel
from typing import Dict, Any, Literal

class CoreRequest(BaseModel):
    """Request model for the core gateway endpoint"""
    module: Literal["finance", "education", "creator", "sample_text"]
    intent: Literal["generate", "analyze", "review"] 
    user_id: str
    data: Dict[str, Any]

class CoreResponse(BaseModel):
    """Response model for the core gateway endpoint"""
    status: str
    message: str
    result: Any