from typing import TypedDict, Literal


class EmailExecutionResult(TypedDict):
    success: bool
    provider: Literal["smtp", "mock"]
    recipient: str | None
    subject: str | None
    trace_id: str
    error_code: str | None
