from typing import Dict, Any


class SimulationRuntimeInputNormalizer:
    """Converts simulation runtime payloads into prompt text."""

    def normalize(self, runtime_input: Dict[str, Any]) -> str:
        scenario = runtime_input.get("scenario", "default simulation")
        constraints = runtime_input.get("constraints", "no constraints")
        return f"Run simulation scenario '{scenario}' with constraints: {constraints}"
