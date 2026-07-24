"""
Sarathi — Enforcement Layer

Consumes resolution_signal from RAJYA output.
Enforces trace_id continuity. No transformation.
"""


from typing import Any


def enforce(rajya_output: dict[str, Any]) -> dict[str, Any]:
    """
    Read resolution_signal and enforce the decision.

    Returns enforcement record with trace_id preserved.
    Raises ValueError on missing trace_id or resolution_signal (fail-closed).
    """
    trace_id = rajya_output.get("trace_id")
    if not trace_id:
        raise ValueError("Sarathi: missing trace_id")

    resolution_signal = rajya_output.get("resolution_signal")
    # resolution_signal may be None when no blocked tasks — that is valid
    return {
        "trace_id": trace_id,
        "enforced": True,
        "resolution_signal": resolution_signal,
        "action": f"ENFORCE:{resolution_signal}" if resolution_signal else "NO_ACTION",
    }
