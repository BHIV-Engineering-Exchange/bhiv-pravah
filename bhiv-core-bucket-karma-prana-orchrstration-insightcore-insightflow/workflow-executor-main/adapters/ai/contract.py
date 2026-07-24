from typing import TypedDict, Literal, Any


class AIExecutionResult(TypedDict):
    success: bool
    provider: Literal["openai", "mock"]
    request_payload: dict
    response: Any | None
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    error_code: str | None
