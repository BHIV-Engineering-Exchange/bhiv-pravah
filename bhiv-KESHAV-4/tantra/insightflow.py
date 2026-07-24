"""
InsightFlow — Observability Layer

Read-only. Emits structured events from KESHAV output.
Never mutates core output. Exposes traces, failures, and execution visibility.
Thread-safe: event list mutations are protected by a lock.
Bounded: retains at most MAX_EVENTS entries (oldest evicted first).
"""

import logging
import threading
from typing import Any

logger = logging.getLogger("insightflow")

MAX_EVENTS = 10_000

_events: list[dict[str, Any]] = []
_lock = threading.Lock()


def emit(keshav_output: dict[str, Any]) -> None:
    """
    Emit a structured observability event from KESHAV output.
    Read-only: does not modify keshav_output.
    """
    if keshav_output.get("status") == "FAIL":
        event = {
            "type": "FAILURE",
            "trace_id": keshav_output.get("trace_id", ""),
            "reason": keshav_output.get("reason"),
        }
        logger.warning("insightflow | %s", event)
    else:
        event = {
            "type": "EXECUTION",
            "trace_id": keshav_output.get("trace_id"),
            "root_cause": keshav_output.get("root_cause"),
            "impact_score": keshav_output.get("impact_score"),
            "severity": keshav_output.get("severity"),
            "resolution_signal": keshav_output.get("resolution_signal"),
        }
        logger.info("insightflow | %s", event)

    with _lock:
        if len(_events) >= MAX_EVENTS:
            _events.pop(0)
        _events.append(event)


def get_events() -> list[dict]:
    """Return all emitted events (read-only copy)."""
    with _lock:
        return list(_events)


def get_failures() -> list[dict]:
    """Return only failure events."""
    with _lock:
        return [e for e in _events if e["type"] == "FAILURE"]


def clear() -> None:
    """Reset event log — for test isolation only."""
    with _lock:
        _events.clear()
