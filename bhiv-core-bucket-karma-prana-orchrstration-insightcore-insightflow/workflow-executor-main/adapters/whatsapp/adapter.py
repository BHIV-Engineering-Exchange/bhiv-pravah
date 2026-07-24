"""
WhatsApp Execution Adapter — Phase E

Deterministic, demo-safe WhatsApp execution.
Mock bridge layer (Twilio / Meta compatible shape).
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from adapters.base import BaseAdapter


class WhatsAppAdapter(BaseAdapter):
    """
    Deterministic WhatsApp Execution Adapter.
    """

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trace_id = payload.get("trace_id")
        recipient = payload.get("recipient")
        message = payload.get("message")

        # -------------------------------
        # Validation (HARD FAIL)
        # -------------------------------
        if not recipient:
            return {
                "success": False,
                "error_code": "missing_recipient",
                "message": "recipient phone number is required",
            }

        if not message:
            return {
                "success": False,
                "error_code": "missing_message",
                "message": "message content is required",
            }

        # -------------------------------
        # Deterministic Execution
        # -------------------------------
        whatsapp_id = f"wa_{uuid.uuid4().hex[:8]}"
        sent_at = datetime.utcnow().isoformat() + "Z"

        # NOTE:
        # Production swap targets:
        # - Twilio WhatsApp API
        # - Meta WhatsApp Cloud API
        # Response shape MUST remain unchanged

        return {
            "success": True,
            "whatsapp_message_id": whatsapp_id,
            "recipient": recipient,
            "message": message,
            "status": "SENT",
            "sent_at": sent_at,
            "trace_id": trace_id,
        }
