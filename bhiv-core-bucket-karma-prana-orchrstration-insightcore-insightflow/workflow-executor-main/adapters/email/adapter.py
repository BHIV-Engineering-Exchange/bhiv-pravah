"""
Email Execution Adapter — Phase E

Deterministic, demo-safe email execution.
Uses mock SMTP-style execution with audit-safe response.
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from adapters.base import BaseAdapter


class EmailAdapter(BaseAdapter):
    """
    Deterministic Email Execution Adapter.
    """

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trace_id = payload.get("trace_id")
        recipient = payload.get("recipient")
        subject = payload.get("subject")
        body = payload.get("body")

        # -------------------------------
        # Validation (HARD FAIL)
        # -------------------------------
        if not recipient:
            return {
                "success": False,
                "error_code": "missing_recipient",
                "message": "recipient email is required",
            }

        if not subject:
            return {
                "success": False,
                "error_code": "missing_subject",
                "message": "email subject is required",
            }

        if not body:
            return {
                "success": False,
                "error_code": "missing_body",
                "message": "email body is required",
            }

        # -------------------------------
        # Deterministic Execution
        # -------------------------------
        message_id = f"email_{uuid.uuid4().hex[:8]}"
        sent_at = datetime.utcnow().isoformat() + "Z"

        # NOTE:
        # In production, this block swaps to:
        # - Gmail API
        # - Microsoft Graph
        # - Hardened SMTP
        # without changing response shape

        return {
            "success": True,
            "message_id": message_id,
            "recipient": recipient,
            "subject": subject,
            "status": "SENT",
            "sent_at": sent_at,
            "trace_id": trace_id,
        }
