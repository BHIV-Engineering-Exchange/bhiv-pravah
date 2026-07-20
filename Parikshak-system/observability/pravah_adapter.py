"""
pravah_adapter.py
==================
Pravah Bhiv observation adapter for Parikshak-system.

Provides a lightweight, fire-and-forget telemetry emitter that pushes signed
runtime signals to the Pravah Control Plane.

Pravah observes — not owns — the execution of this system.

Usage:
    from observability.pravah_adapter import emit_pravah_signal

    emit_pravah_signal(state="running", latency_ms=95.0)
    emit_pravah_signal(state="error", errors_last_min=3)

Environment:
    PRAVAH_URL          URL of the Pravah Control Plane runtime endpoint
                        Default: http://localhost:7000/api/runtime
    SSPL_SECRET_KEY     Shared secret for HMAC-SHA256 payload signing
                        Default: default-secret-key-change-in-prod
"""

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import uuid

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — resolved from environment at import time
# ---------------------------------------------------------------------------
PRAVAH_URL = os.getenv("PRAVAH_URL", "http://localhost:7000/api/runtime")
SSPL_SECRET = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
APP_NAME = "parikshak-system"


# ---------------------------------------------------------------------------
# Signature helper
# ---------------------------------------------------------------------------

def _sign_payload(trace_id: str, canonical: str) -> tuple[str, str]:
    """Return (timestamp, signature) for a canonical JSON payload."""
    body_hash = hashlib.sha256(canonical.encode()).hexdigest()
    timestamp = str(int(time.time()))
    sig_data = f"{trace_id}:{timestamp}:{body_hash}"
    signature = hmac.new(
        SSPL_SECRET.encode(),
        sig_data.encode(),
        hashlib.sha256,
    ).hexdigest()
    return timestamp, signature


# ---------------------------------------------------------------------------
# Core emitter — non-blocking, fire-and-forget
# ---------------------------------------------------------------------------

def _send(payload: dict) -> None:
    """Internal: send telemetry to Pravah in a background thread. Never raises."""
    try:
        import requests as _req
    except ImportError:
        logger.debug("[Pravah] 'requests' not installed — telemetry skipped")
        return

    trace_id = f"parikshak-{uuid.uuid4().hex[:16]}"
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    timestamp, signature = _sign_payload(trace_id, canonical)

    headers = {
        "X-Trace-Id": trace_id,
        "X-Timestamp": timestamp,
        "X-Trace-Signature": signature,
        "Content-Type": "application/json",
    }

    try:
        resp = _req.post(PRAVAH_URL, json=payload, headers=headers, timeout=4)
        logger.debug(
            "[Pravah] Telemetry sent | trace=%s app=%s status=%s",
            trace_id, APP_NAME, resp.status_code,
        )
    except Exception as exc:
        # Pravah observer must NEVER impact the normal operation.
        # Swallow all errors silently.
        logger.debug("[Pravah] Telemetry failed (non-critical): %s", exc)


def emit_pravah_signal(
    state: str = "running",
    latency_ms: float = 0.0,
    errors_last_min: int = 0,
    workers: int = 1,
    extra: dict | None = None,
) -> None:
    """
    Emit a signed runtime telemetry signal to Pravah asynchronously.

    This call is fire-and-forget — it never blocks the caller, never raises,
    and has zero impact on response time or reliability.

    Args:
        state:           Runtime state string ("running", "degraded", "error")
        latency_ms:      Request or operation latency in milliseconds
        errors_last_min: Number of errors observed in the last minute
        workers:         Number of active worker processes/threads
        extra:           Optional dict of additional fields to include in payload
    """
    payload = {
        "app": APP_NAME,
        "env": os.getenv("ENVIRONMENT", "dev"),
        "state": state,
        "latency_ms": round(latency_ms, 2),
        "errors_last_min": errors_last_min,
        "workers": workers,
    }
    if extra:
        payload.update(extra)

    t = threading.Thread(target=_send, args=(payload,), daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Optional background heartbeat — call start_heartbeat() once at startup
# ---------------------------------------------------------------------------

_heartbeat_running = False


def start_heartbeat(interval_seconds: int = 60) -> None:
    """
    Start a background thread that pings Pravah every `interval_seconds`.
    Call once from app startup. Idempotent — safe to call multiple times.

    Pravah observes — not owns — this runtime.
    """
    global _heartbeat_running
    if _heartbeat_running:
        return
    _heartbeat_running = True

    def _loop():
        while True:
            time.sleep(interval_seconds)
            emit_pravah_signal(state="running")

    t = threading.Thread(target=_loop, daemon=True, name="pravah-parikshak-heartbeat")
    t.start()
    logger.info(
        "[Pravah] Parikshak heartbeat started — emitting every %ds to %s",
        interval_seconds, PRAVAH_URL,
    )
