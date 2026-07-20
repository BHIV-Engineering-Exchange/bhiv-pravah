from typing import Dict, Any


class GurukulInputNormalizer:
    """Converts Gurukul requests into canonical prompt text."""

    def normalize(self, gurukul_input: Dict[str, Any]) -> str:
        topic = gurukul_input.get("topic", "general learning")
        level = gurukul_input.get("level", "intermediate")
        objective = gurukul_input.get("objective", "create lesson plan")
        return f"{objective} for {topic} at {level} level"
