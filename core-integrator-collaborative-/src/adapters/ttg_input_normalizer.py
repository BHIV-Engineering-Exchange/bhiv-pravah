"""
TTG Input Normalizer
===================
Converts TTG-specific inputs into Prompt Runner-compatible format.

STRICT RULES:
- NO direct Core calls
- NO execution logic
- ONLY input transformation
"""

from typing import Dict, Any


class TTGInputNormalizer:
    """Normalizes TTG inputs to unified prompt format"""
    
    def normalize(self, ttg_input: Dict[str, Any]) -> str:
        """
        Convert TTG input to prompt string
        
        TTG Input Format:
        {
            "game_type": "adventure",
            "theme": "fantasy",
            "difficulty": "medium",
            "player_count": 2,
            "description": "Create a dungeon crawler game"
        }
        
        Output: Unified prompt string for Prompt Runner
        """
        game_type = ttg_input.get("game_type", "general")
        theme = ttg_input.get("theme", "")
        difficulty = ttg_input.get("difficulty", "medium")
        description = ttg_input.get("description", "")
        player_count = ttg_input.get("player_count", 1)
        
        # Build unified prompt
        prompt_parts = []
        
        if description:
            prompt_parts.append(description)
        else:
            prompt_parts.append(f"Create a {game_type} game")
        
        if theme:
            prompt_parts.append(f"with {theme} theme")
        
        prompt_parts.append(f"for {player_count} player(s)")
        prompt_parts.append(f"at {difficulty} difficulty level")
        
        unified_prompt = " ".join(prompt_parts)
        
        return unified_prompt
    
    def validate_ttg_input(self, data: Dict[str, Any]) -> bool:
        """Validate TTG input structure"""
        required_fields = ["game_type"]
        return all(field in data for field in required_fields)
