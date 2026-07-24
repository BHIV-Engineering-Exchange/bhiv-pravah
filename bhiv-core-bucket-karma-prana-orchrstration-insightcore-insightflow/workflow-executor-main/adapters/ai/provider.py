class AIProvider:
    """
    Deterministic AI provider wrapper.

    NOTE:
    - Output content may vary in real systems
    - Execution behavior MUST NOT
    """

    def call(self, payload: dict) -> dict:
        prompt = payload.get("prompt")

        if not prompt:
            return {
                "success": False,
                "error_code": "missing_prompt",
                "response": None,
            }

        # Deterministic mock response
        return {
            "success": True,
            "response": {
                "text": f"[MOCK_AI_RESPONSE] {prompt}"
            },
        }
