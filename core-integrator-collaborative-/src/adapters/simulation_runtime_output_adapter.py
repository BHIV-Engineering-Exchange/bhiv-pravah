from typing import Dict, Any


class SimulationRuntimeOutputAdapter:
    """Transforms runtime output for simulation runtime consumers."""

    def transform(self, core_output: Dict[str, Any]) -> Dict[str, Any]:
        result = core_output.get("result", {})
        return {
            "simulation_result": result,
            "status": core_output.get("status", "unknown"),
            "message": core_output.get("message", ""),
        }
