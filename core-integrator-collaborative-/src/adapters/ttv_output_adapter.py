"""
TTV Output Adapter
=================
Transforms Core output into TTV-specific format.

CRITICAL RULES:
- Core output remains UNCHANGED
- Adapter operates OUTSIDE Core
- NO modification of Core logic
- THIN transformation layer only
"""

from typing import Dict, Any, List


class TTVOutputAdapter:
    """Adapts Core output for TTV consumption"""
    
    def transform(self, core_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Core output to TTV format
        
        Core Output (unchanged):
        {
            "status": "success",
            "message": "...",
            "result": {...},
            "execution_envelope": {...}
        }
        
        TTV Output:
        {
            "video_script": {...},
            "audio_requirements": {...},
            "visual_elements": {...},
            "metadata": {...}
        }
        """
        result = core_output.get("result", {})
        execution_envelope = core_output.get("execution_envelope", {})
        
        # Extract relevant data for TTV
        ttv_output = {
            "video_script": self._extract_video_script(result),
            "audio_requirements": self._extract_audio_requirements(result),
            "visual_elements": self._extract_visual_elements(result),
            "timeline": self._extract_timeline(result),
            "metadata": {
                "execution_id": execution_envelope.get("execution_id"),
                "trace_id": execution_envelope.get("trace_id"),
                "timestamp": execution_envelope.get("timestamp_utc"),
                "status": core_output.get("status")
            }
        }
        
        return ttv_output
    
    def _extract_video_script(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract video script from Core result"""
        return {
            "title": result.get("title", "Untitled Video"),
            "narration": result.get("narration", ""),
            "scenes": result.get("scenes", []),
            "dialogue": result.get("dialogue", []),
            "captions": result.get("captions", [])
        }
    
    def _extract_audio_requirements(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract audio requirements"""
        return {
            "voice_type": result.get("voice_type", "neutral"),
            "background_music": result.get("background_music", "none"),
            "sound_effects": result.get("sound_effects", []),
            "audio_style": result.get("audio_style", "standard")
        }
    
    def _extract_visual_elements(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract visual elements"""
        return {
            "style": result.get("visual_style", "standard"),
            "animations": result.get("animations", []),
            "transitions": result.get("transitions", []),
            "graphics": result.get("graphics", []),
            "text_overlays": result.get("text_overlays", [])
        }
    
    def _extract_timeline(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract video timeline"""
        return result.get("timeline", [
            {"timestamp": "0:00", "event": "intro"},
            {"timestamp": "0:05", "event": "main_content"},
            {"timestamp": "0:55", "event": "outro"}
        ])
