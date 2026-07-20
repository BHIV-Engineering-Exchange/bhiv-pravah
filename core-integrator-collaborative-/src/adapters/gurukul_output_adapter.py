from typing import Dict, Any


class GurukulOutputAdapter:
    """Transforms runtime output for Gurukul consumers."""

    def transform(self, core_output: Dict[str, Any]) -> Dict[str, Any]:
        result = core_output.get("result", {})
        return {
            "lesson_plan": result.get("lesson_plan", result),
            "assessment": result.get("assessment", {}),
            "metadata": {"status": core_output.get("status", "unknown")},
        }
