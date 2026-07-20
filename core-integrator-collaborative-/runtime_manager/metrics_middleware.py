"""Shared request metrics middleware."""

from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Any, Dict

_METRICS = {
    "started_at": time.time(),
    "total_requests": 0,
    "error_requests": 0,
    "latency_ms_window": deque(maxlen=2000),
    "requests_timestamps": deque(maxlen=2000),
}
_LOCK = Lock()


async def request_metrics_middleware(request, call_next):
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        now = time.time()
        with _LOCK:
            _METRICS["total_requests"] += 1
            if status_code >= 400:
                _METRICS["error_requests"] += 1
            _METRICS["latency_ms_window"].append(elapsed_ms)
            _METRICS["requests_timestamps"].append(now)


def _percentile(values, pct: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = max(0, min(len(vals) - 1, int((pct / 100.0) * (len(vals) - 1))))
    return round(vals[idx], 3)


def get_local_metrics_snapshot() -> Dict[str, Any]:
    with _LOCK:
        now = time.time()
        one_minute_ago = now - 60
        req_last_min = [t for t in _METRICS["requests_timestamps"] if t >= one_minute_ago]
        total = _METRICS["total_requests"]
        errors = _METRICS["error_requests"]
        lat = list(_METRICS["latency_ms_window"])
    return {
        "uptime_seconds": round(now - _METRICS["started_at"], 3),
        "total_requests": total,
        "error_requests": errors,
        "error_rate_pct": round((errors / total * 100.0), 3) if total else 0.0,
        "requests_per_minute": len(req_last_min),
        "latency_ms": {
            "p50": _percentile(lat, 50),
            "p95": _percentile(lat, 95),
        },
    }
