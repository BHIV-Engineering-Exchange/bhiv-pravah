"""
Bucket — Truth Layer

Stores verifiable execution output. Write only on successful runs.
Fail-closed: rejects writes if trace_id is missing.
Read-only retrieval for verification.
Thread-safe: all mutations are protected by a lock.
Bounded: retains at most MAX_ENTRIES entries (oldest evicted first).
"""

import logging
import threading

logger = logging.getLogger("bucket")

MAX_ENTRIES = 50_000

_store: dict[str, dict] = {}
_insertion_order: list[str] = []
_lock = threading.Lock()


def write(core_output: dict, keshav_output: dict) -> None:
    """
    Persist execution truth. Raises ValueError on missing trace_id (fail-closed).
    No write on failure — caller must not invoke this on failed runs.
    """
    trace_id = core_output.get("trace_id")
    if not trace_id:
        raise ValueError("Bucket: missing trace_id — write rejected")

    with _lock:
        if trace_id not in _store:
            if len(_store) >= MAX_ENTRIES:
                oldest = _insertion_order.pop(0)
                _store.pop(oldest, None)
            _insertion_order.append(trace_id)
        _store[trace_id] = {
            "trace_id": trace_id,
            "keshav_output": keshav_output,
            "core_output": core_output,
        }
    logger.info("bucket | write trace_id=%s", trace_id)


def read(trace_id: str) -> dict | None:
    """Retrieve stored truth by trace_id. Returns None if not found."""
    with _lock:
        return _store.get(trace_id)


def clear() -> None:
    """Reset store — for test isolation only."""
    with _lock:
        _store.clear()
        _insertion_order.clear()


def all_trace_ids() -> list[str]:
    """Return all stored trace_ids."""
    with _lock:
        return list(_store.keys())
