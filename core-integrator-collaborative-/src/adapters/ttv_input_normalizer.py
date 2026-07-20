"""
TTV Input Normalizer
===================
Converts TTV-specific inputs into Prompt Runner-compatible format.

STRICT RULES:
- NO direct Core calls
- NO execution logic
- ONLY input transformation
"""

from typing import Dict, Any


class TTVInputNormalizer:
    """Normalizes TTV inputs to unified prompt format"""
    
    def normalize(self, ttv_input: Dict[str, Any]) -> str:
        """
        Convert TTV input to prompt string
        
        TTV Input Format:
        {
            "video_type": "tutorial",
            "topic": "Python programming",
            "duration": "5min",
            "style": "animated",
            "voice": "professional",
            "description": "Create a Python basics tutorial video"
        }
        
        Output: Unified prompt string for Prompt Runner
        """
        video_type = ttv_input.get("video_type", "general")
        topic = ttv_input.get("topic", "")
        duration = ttv_input.get("duration", "5min")
        style = ttv_input.get("style", "standard")
        voice = ttv_input.get("voice", "neutral")
        description = ttv_input.get("description", "")
        
        # Build unified prompt
        prompt_parts = []
        
        if description:
            prompt_parts.append(description)
        else:
            prompt_parts.append(f"Create a {video_type} video")
        
        if topic:
            prompt_parts.append(f"about {topic}")
        
        prompt_parts.append(f"with {duration} duration")
        prompt_parts.append(f"in {style} style")
        prompt_parts.append(f"using {voice} voice")
        
        unified_prompt = " ".join(prompt_parts)
        
        return unified_prompt
    
    def validate_ttv_input(self, data: Dict[str, Any]) -> bool:
        """Validate TTV input structure"""
        required_fields = ["video_type"]
        return all(field in data for field in required_fields)
