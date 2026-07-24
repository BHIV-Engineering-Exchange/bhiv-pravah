class EmailProvider:
    """
    Deterministic email provider (mock).

    Real SMTP/Gmail can replace this later.
    """

    def send(self, *, recipient: str, subject: str, body: str) -> dict:
        if not recipient or not subject or not body:
            return {
                "success": False,
                "error_code": "invalid_email_payload",
            }

        # Deterministic mock success
        return {
            "success": True,
        }
