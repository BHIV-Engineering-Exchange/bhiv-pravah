import os
import uuid
import time
import hmac
import hashlib
import json
import logging
import threading

logger = logging.getLogger(__name__)

PRAVAH_URL = os.getenv("PRAVAH_URL", "http://localhost:7000/api/runtime")
SSPL_SECRET = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
APP_NAME = "bhiv-insight-core"

def _sign_payload(trace_id: str, canonical: str) -> tuple[str, str]:
    body_hash = hashlib.sha256(canonical.encode()).hexdigest()
    timestamp = str(int(time.time()))
    sig_data = f"{trace_id}:{timestamp}:{body_hash}"
    signature = hmac.new(SSPL_SECRET.encode(), sig_data.encode(), hashlib.sha256).hexdigest()
    return timestamp, signature

def _send(payload: dict) -> None:
    try:
        import requests as _req
    except ImportError:
        return

    trace_id = f"bhiv-{uuid.uuid4().hex[:16]}"
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    timestamp, signature = _sign_payload(trace_id, canonical)

    headers = {
        "X-Trace-Id": trace_id,
        "X-Timestamp": timestamp,
        "X-Trace-Signature": signature,
        "Content-Type": "application/json",
    }

    try:
        _req.post(PRAVAH_URL, json=payload, headers=headers, timeout=3)
    except Exception:
        pass

def emit_pravah_signal(
    state: str = "running",
    latency_ms: float = 0.0,
    errors_last_min: int = 0,
    workers: int = 1,
    extra: dict | None = None,
) -> None:
    payload = {
        "app": APP_NAME,
        "env": os.getenv("ENVIRONMENT", "dev"),
        "state": state,
        "latency_ms": int(latency_ms),
        "errors_last_min": int(errors_last_min),
        "workers": int(workers),
    }
    if extra:
        payload.update(extra)

    threading.Thread(target=_send, args=(payload,), daemon=True).start()

_heartbeat_running = False

def start_heartbeat(interval_seconds: int = 60) -> None:
    global _heartbeat_running
    if _heartbeat_running:
        return
    _heartbeat_running = True

    def _loop():
        while True:
            try:
                emit_pravah_signal(state="running")
            except Exception:
                pass
            time.sleep(interval_seconds)

    threading.Thread(target=_loop, daemon=True).start()
