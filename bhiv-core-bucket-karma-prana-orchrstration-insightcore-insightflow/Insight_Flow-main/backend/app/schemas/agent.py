from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class AgentCapabilitySchema(BaseModel):
    """Schema for agent capability"""
    name: str
    description: str
    confidence_threshold: float = 0.7


class AgentCreate(BaseModel):
    """Schema for creating agent"""
    name: str
    type: str = Field(..., description="Agent type: nlp, tts, rl, computer_vision, etc.")
    status: str = Field(default="active", description="Agent status: active, inactive, maintenance")
    capabilities: List[AgentCapabilitySchema] = []
    tags: List[str] = []
    metadata: Dict = {}


class AgentResponse(BaseModel):
    """Schema for agent response"""
    id: str
    name: str
    type: str
    status: str
    capabilities: List[Dict] = []
    performance_score: float
    success_rate: float
    average_latency: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    tags: List[str]
    metadata: Dict
    created_at: Optional[str] = None
    updated_at: Optional[str] = None