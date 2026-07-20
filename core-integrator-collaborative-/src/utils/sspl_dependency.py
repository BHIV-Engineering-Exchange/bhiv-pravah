from fastapi import Request, HTTPException
from typing import Optional
from . import sspl as sspl_module
from ..db.nonce_store import NonceStore
from config.config import SSPL_ALLOW_DRIFT_SECONDS
import logging

logger = logging.getLogger(__name__)


nonce_store = NonceStore()


async def require_sspl(request: Request):
    """FastAPI dependency that enforces timestamp freshness and nonce anti-replay.

    Signature verification is attempted only if PyNaCl is installed; otherwise
    the dependency logs a warning and allows the request to proceed (option B).
    """
    # Expect timestamp and nonce in headers or JSON body
    hdr_ts = request.headers.get("X-SSPL-Timestamp")
    hdr_nonce = request.headers.get("X-SSPL-Nonce")
    hdr_pubid = request.headers.get("X-SSPL-PubId")
    hdr_sig = request.headers.get("X-SSPL-Signature")

    body = None
    try:
        body = await request.json()
    except Exception:
        body = None

    ts = hdr_ts or (body and body.get("timestamp"))
    nonce = hdr_nonce or (body and body.get("nonce"))

    # Basic checks
    if not ts or not nonce:
        raise HTTPException(status_code=400, detail="Missing SSPL timestamp or nonce")

    # Timestamp freshness
    if not sspl_module.SSPL.timestamp_fresh(ts, window_seconds=SSPL_ALLOW_DRIFT_SECONDS):
        raise HTTPException(status_code=401, detail="Stale timestamp")

    # Nonce anti-replay
    if not nonce_store.use_nonce(nonce):
        raise HTTPException(status_code=409, detail="Nonce already used")

    # Signature verification (optional)
    if sspl_module.VerifyKey is None:
        logger.warning("PyNaCl not available: SSPL signature verification is disabled")
        return True

    # If signature header/body missing, reject
    signature = hdr_sig or (body and body.get("signature"))
    public_key_b64 = hdr_pubid or (body and body.get("public_key"))
    if not signature or not public_key_b64:
        raise HTTPException(status_code=400, detail="Missing signature/public key")

    # Build canonical message: prefer raw body bytes if available
    if body is not None:
        import json
        msg_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        # fallback to path + query
        msg_bytes = (request.url.path + "?" + str(request.query_params)).encode("utf-8")

    try:
        ok = sspl_module.verify_signature(public_key_b64, msg_bytes, signature)
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid signature")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True
