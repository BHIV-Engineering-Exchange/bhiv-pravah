"""
TTG Output Adapter
=================
Transforms Core output into TTG-specific format.

CRITICAL RULES:
- Core output remains UNCHANGED
- Adapter operates OUTSIDE Core
- NO modification of Core logic
- THIN transformation layer only
"""

from typing import Dict, Any


class TTGOutputAdapter:
    """Adapts Core output for TTG consumption"""
    
    def transform(self, core_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Core output to TTG format
        
        Core Output (unchanged):
        {
            "status": "success",
            "message": "...",
            "result": {...},
            "execution_envelope": {...}
        }
        
        TTG Output:
        {
            "game_content": {...},
            "gameplay_structure": {...},
            "assets": {...},
            "metadata": {...}
        }
        """
        result = core_output.get("result", {})
        execution_envelope = core_output.get("execution_envelope", {})
        
        # Extract relevant data for TTG
        ttg_output = {
            "game_content": self._extract_game_content(result),
            "gameplay_structure": self._extract_gameplay_structure(result),
            "assets": self._extract_assets(result),
            "metadata": {
                "execution_id": execution_envelope.get("execution_id"),
                "trace_id": execution_envelope.get("trace_id"),
                "timestamp": execution_envelope.get("timestamp_utc"),
                "status": core_output.get("status")
            }
        }
        
        return ttg_output
    
    def _extract_game_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract game content from Core result"""
        return {
            "title": result.get("title", "Untitled Game"),
            "description": result.get("description", ""),
            "genre": result.get("genre", "general"),
            "mechanics": result.get("mechanics", []),
            "objectives": result.get("objectives", [])
        }
    
    def _extract_gameplay_structure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract gameplay structure"""
        return {
            "levels": result.get("levels", []),
            "progression": result.get("progression", {}),
            "difficulty_curve": result.get("difficulty_curve", "linear"),
            "player_actions": result.get("player_actions", [])
        }
    
    def _extract_assets(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract asset requirements"""
        return {
            "characters": result.get("characters", []),
            "environments": result.get("environments", []),
            "items": result.get("items", []),
            "audio": result.get("audio", {})
        }
