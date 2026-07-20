"""
Sovereign Fusion Layer Schemas

Request and response models for the Sovereign Polyglot Fusion Layer API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class SovereignInferRequest(BaseModel):
    """Request model for /sovereign/infer endpoint"""
    
    text: str = Field(..., description="Input text to process")
    lang: str = Field(default="en", description="Source language code (e.g., 'en', 'hi', 'es')")
    target_lang: Optional[str] = Field(default=None, description="Target language code for translation")
    tone: Optional[str] = Field(default="neutral", description="Tone for output (neutral, excited, formal, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "What is mathematics?",
                "lang": "en",
                "target_lang": "hi",
                "tone": "educational"
            }
        }


class PipelineStage(BaseModel):
    """Information about a pipeline stage"""
    
    stage_name: str
    status: str  # "success", "error", "skipped"
    output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None


class SovereignInferResponse(BaseModel):
    """Response model for /sovereign/infer endpoint"""
    
    output: str = Field(..., description="Final processed output text")
    target_lang: str = Field(..., description="Language of the output")
    pipeline_stages: List[PipelineStage] = Field(..., description="Details of each pipeline stage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "output": "गणित क्या है?",
                "target_lang": "hi",
                "pipeline_stages": [
                    {
                        "stage_name": "lm_core",
                        "status": "success",
                        "processing_time_ms": 150.5
                    }
                ],
                "metadata": {}
            }
        }


