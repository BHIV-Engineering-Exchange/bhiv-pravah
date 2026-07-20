"""
Vaani RL-TTS Router

Endpoints for Vaani reinforcement learning text-to-speech system.
Focused on Arabic language prosody mapping and TTS generation.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services.pravah_adapter import pravah_adapter
from app.services.prosody_mapper import (
    generate_prosody_hint,
    validate_prosody_hint,
    get_available_tones,
    map_language_to_prosody
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProsodyMapRequest(BaseModel):
    """Request model for /compose/prosody_map endpoint"""
    
    text: str = Field(..., description="Text to generate prosody for")
    language: str = Field(default="ar", description="Language code (e.g., 'ar' for Arabic)")
    tone: str = Field(default="neutral", description="Tone/style (neutral, excited, educational, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "ما هي الرياضيات؟",
                "language": "ar",
                "tone": "educational"
            }
        }


class ProsodyMapResponse(BaseModel):
    """Response model for /compose/prosody_map endpoint"""
    
    prosody_hint: str = Field(..., description="Prosody hint identifier")
    prosody_config: Dict[str, Any] = Field(..., description="Complete prosody configuration")
    language: str
    tone: str
    validated: bool = Field(..., description="Whether prosody hint is valid")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prosody_hint": "educational_ar",
                "prosody_config": {
                    "pitch": 0.55,
                    "speed": 0.95,
                    "emphasis": 0.4,
                    "pause_duration": 0.25
                },
                "language": "ar",
                "tone": "educational",
                "validated": True
            }
        }


@router.post("/compose/prosody_map", response_model=ProsodyMapResponse)
async def compose_prosody_map(request: ProsodyMapRequest):
    """
    Generate prosody hint for text based on language and tone
    
    This endpoint maps language and tone to prosody configuration
    that will be used by Vaani RL-TTS for natural speech generation.
    
    Args:
        request: ProsodyMapRequest with text, language, and tone
        
    Returns:
        ProsodyMapResponse with prosody hint and configuration
    """
    try:
        # Emit Signal: Prosody Mapping Started
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="prosody_mapping_started",
            payload={"lang": request.language, "tone": request.tone}
        )

        # Generate prosody hint
        prosody_config = generate_prosody_hint(
            text=request.text,
            lang=request.language,
            tone=request.tone
        )
        
        if not prosody_config:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate prosody for language: {request.language}, tone: {request.tone}"
            )
        
        # Validate prosody hint
        is_valid = validate_prosody_hint(prosody_config)
        
        # Emit Signal: Prosody Mapping Success
        pravah_adapter.emit_signal(
            event_type="voice_action",
            action="prosody_mapping_success",
            status="success",
            payload={"prosody_hint": prosody_hint}
        )

        return ProsodyMapResponse(
            prosody_hint=prosody_hint,
            prosody_config=prosody_config,
            language=request.language,
            tone=request.tone,
            validated=is_valid
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prosody mapping failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prosody mapping failed: {str(e)}"
        )


@router.get("/tones/{language}")
async def get_tones_for_language(language: str):
    """
    Get available tones for a language
    
    Args:
        language: Language code
        
    Returns:
        dict: List of available tones
    """
    try:
        tones = get_available_tones(language)
        return {
            "language": language,
            "available_tones": tones,
            "count": len(tones)
        }
    except Exception as e:
        logger.error(f"Failed to get tones: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tones: {str(e)}"
        )


@router.get("/prosody/{language}/{tone}")
async def get_prosody_config(language: str, tone: str):
    """
    Get prosody configuration for language and tone
    
    Args:
        language: Language code
        tone: Tone name
        
    Returns:
        dict: Prosody configuration
    """
    try:
        prosody = map_language_to_prosody(language, tone)
        
        if not prosody:
            raise HTTPException(
                status_code=404,
                detail=f"Prosody not found for language: {language}, tone: {tone}"
            )
        
        return {
            "language": language,
            "tone": tone,
            "prosody": prosody,
            "validated": validate_prosody_hint(prosody)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prosody config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prosody config: {str(e)}"
        )

