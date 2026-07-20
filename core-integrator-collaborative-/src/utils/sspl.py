import time
import base64
from typing import Optional

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
except Exception:
    VerifyKey = None
    BadSignatureError = Exception


class SSPL:
    """Minimal SSPL helpers: verify Ed25519 signatures and basic timestamp/nonce checks.

    This is a lightweight scaffolding suitable for Day 3 development. For
    production use, install `pynacl` and expand tests/validation.
    """

    @staticmethod
    def verify_signature(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
        if VerifyKey is None:
            raise RuntimeError("pynacl not installed; cannot verify signatures")

        try:
            vk = VerifyKey(base64.b64decode(public_key_b64))
            vk.verify(message, base64.b64decode(signature_b64))
            return True
        except BadSignatureError:
            return False

    @staticmethod
    def timestamp_fresh(ts_iso: str, window_seconds: int = 300) -> bool:
        try:
            ts = float(ts_iso)
        except Exception:
            return False
        now = time.time()
        return abs(now - ts) <= window_seconds


# Convenience top-level function for tests and callers
def verify_signature(public_key_b64: str, message: bytes, signature_b64: str) -> bool:
    return SSPL.verify_signature(public_key_b64, message, signature_b64)
