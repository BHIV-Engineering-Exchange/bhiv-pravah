from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Agent type enumeration"""
    NLP = "nlp"
    TTS = "tts"
    RL = "reinforcement_learning"
    CV = "computer_vision"
    AUDIO = "audio_processing"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class AgentCapability(BaseModel):
    """Agent capability model"""
    name: str
    description: str
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class Agent(BaseModel):
    """Agent database model"""
    id: Optional[str] = None
    name: str
    type: AgentType
    status: AgentStatus = AgentStatus.ACTIVE
    capabilities: List[AgentCapability] = []
    performance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    success_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    average_latency: float = Field(default=0.0, ge=0.0)  # in milliseconds
    total_requests: int = Field(default=0, ge=0)
    successful_requests: int = Field(default=0, ge=0)
    failed_requests: int = Field(default=0, ge=0)
    tags: List[str] = []
    metadata: Dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "NLP Processor Agent",
                "type": "nlp",
                "status": "active",
                "capabilities": [
                    {
                        "name": "text_classification",
                        "description": "Classify text into categories",
                        "confidence_threshold": 0.8
                    }
                ],
                "tags": ["text", "classification", "intent"],
                "performance_score": 0.85
            }
        }