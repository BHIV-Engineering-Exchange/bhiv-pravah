import uuid


class WhatsAppProvider:
    """
    Deterministic mock provider.
    Real API (Twilio / Meta) can replace this without changing adapter logic.
    """

    def send_message(self, recipient: str, message: str) -> dict:
        if not recipient or not message:
            return {
                "success": False,
                "error_code": "invalid_payload",
                "message_id": None,
            }

        return {
            "success": True,
            "message_id": f"wa_{uuid.uuid4().hex[:12]}",
        }
