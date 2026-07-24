"""
RAJYA — Decision Layer

Consumes KESHAV output directly. No schema transformation, no adapter.
Contract: accepts the exact dict returned by analyze_and_recommend().
Enforces trace_id continuity — rejects if trace_id is absent or mismatched.
"""


from typing import Any


def consume(keshav_output: dict[str, Any], expected_trace_id: str) -> dict[str, Any]:
    """
    Validate and accept KESHAV output into the decision layer.

    Returns the same dict unchanged (zero transformation).
    Raises ValueError on contract violation (fail-closed).
    """
    if keshav_output.get("status") == "FAIL":
        raise ValueError(
            f"RAJYA: upstream KESHAV failure — {keshav_output.get('reason')}"
        )
    if "trace_id" not in keshav_output:
        raise ValueError("RAJYA: missing trace_id in KESHAV output")
    if keshav_output["trace_id"] != expected_trace_id:
        raise ValueError(
            f"RAJYA: trace_id mismatch — "
            f"expected={expected_trace_id!r} got={keshav_output['trace_id']!r}"
        )
    # Zero transformation: pass through unchanged
    return keshav_output
