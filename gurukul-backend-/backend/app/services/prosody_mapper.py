"""
Prosody Mapper Service

Maps language and tone to prosody hints for Vaani RL-TTS system.
Focused on Arabic language prosody mapping.

Prosody hints control pitch, speed, emphasis, and pauses in text-to-speech
to create natural-sounding, contextually appropriate speech.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global prosody mappings cache
_prosody_cache: Optional[Dict[str, Any]] = None


def _get_prosody_mappings_path() -> Path:
    """Get path to prosody mappings JSON file"""
    return Path(__file__).parent.parent.parent / "data" / "prosody_mappings.json"


def _load_prosody_mappings() -> Dict[str, Any]:
    """
    Load prosody mappings from JSON file
    
    Returns:
        dict: Prosody mappings data
        
    Raises:
        FileNotFoundError: If mappings file doesn't exist
    """
    global _prosody_cache
    
    if _prosody_cache is not None:
        return _prosody_cache
    
    mappings_path = _get_prosody_mappings_path()
    
    if not mappings_path.exists():
        raise FileNotFoundError(
            f"Prosody mappings file not found at {mappings_path}"
        )
    
    with open(mappings_path, 'r', encoding='utf-8') as f:
        _prosody_cache = json.load(f)
    
    logger.info("Prosody mappings loaded successfully")
    return _prosody_cache


def map_language_to_prosody(lang: str, tone: str = "neutral") -> Optional[Dict[str, Any]]:
    """
    Map language and tone to prosody configuration
    
    Args:
        lang: Language code (e.g., 'ar' for Arabic)
        tone: Tone/style (neutral, excited, educational, formal, friendly, calm)
        
    Returns:
        dict: Prosody configuration with pitch, speed, emphasis, etc.
    """
    try:
        mappings = _load_prosody_mappings()
        languages = mappings.get('languages', {})
        
        lang_data = languages.get(lang.lower())
        if not lang_data:
            logger.warning(f"No prosody mappings found for language: {lang}")
            return None
        
        tones = lang_data.get('tones', {})
        tone_data = tones.get(tone.lower())
        
        if not tone_data:
            # Fallback to default tone
            default_tone = lang_data.get('default_tone', 'neutral')
            logger.warning(
                f"Tone '{tone}' not found for {lang}, using default: {default_tone}"
            )
            tone_data = tones.get(default_tone, {})
        
        return {
            **tone_data,
            "language": lang,
            "tone": tone,
            "rtl": lang_data.get('rtl', False)
        }
        
    except Exception as e:
        logger.error(f"Failed to map prosody: {e}")
        return None


def generate_prosody_hint(text: str, lang: str, tone: str = "neutral") -> Dict[str, Any]:
    """
    Generate prosody hint for text based on language and tone
    
    Args:
        text: Text to generate prosody for
        lang: Language code
        tone: Tone/style
        
    Returns:
        dict: Complete prosody hint with metadata
    """
    prosody_config = map_language_to_prosody(lang, tone)
    
    if not prosody_config:
        # Return default prosody if mapping fails
        prosody_config = {
            "pitch": 0.5,
            "speed": 1.0,
            "emphasis": 0.3,
            "pause_duration": 0.2,
            "prosody_hint": "default",
            "language": lang,
            "tone": tone
        }
    
    # Add text-specific adjustments
    text_length = len(text.split())
    
    # Adjust pause duration based on text length
    if text_length > 50:
        prosody_config["pause_duration"] *= 1.2  # Longer pauses for longer text
    
    # Add metadata
    prosody_config["text_length"] = text_length
    prosody_config["word_count"] = text_length
    
    return prosody_config


def validate_prosody_hint(hint: Dict[str, Any]) -> bool:
    """
    Validate prosody hint structure and values
    
    Args:
        hint: Prosody hint dictionary to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["pitch", "speed", "emphasis", "prosody_hint"]
    
    for field in required_fields:
        if field not in hint:
            logger.warning(f"Missing required field in prosody hint: {field}")
            return False
    
    # Validate ranges
    if not (0.0 <= hint.get("pitch", 0) <= 1.0):
        logger.warning("Pitch out of valid range [0.0, 1.0]")
        return False
    
    if not (0.1 <= hint.get("speed", 0) <= 2.0):
        logger.warning("Speed out of valid range [0.1, 2.0]")
        return False
    
    if not (0.0 <= hint.get("emphasis", 0) <= 1.0):
        logger.warning("Emphasis out of valid range [0.0, 1.0]")
        return False
    
    return True


def get_available_tones(lang: str) -> list:
    """
    Get list of available tones for a language
    
    Args:
        lang: Language code
        
    Returns:
        list: Available tone names
    """
    try:
        mappings = _load_prosody_mappings()
        languages = mappings.get('languages', {})
        lang_data = languages.get(lang.lower())
        
        if lang_data:
            return list(lang_data.get('tones', {}).keys())
        
        return []
    except Exception as e:
        logger.error(f"Failed to get available tones: {e}")
        return []

