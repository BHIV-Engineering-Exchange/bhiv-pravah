from typing import TypedDict


class WhatsAppExecutionResult(TypedDict):
    success: bool
    provider: str
    message_id: str | None
    recipient: str | None
    error_code: str | None
