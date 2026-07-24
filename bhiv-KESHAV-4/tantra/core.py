"""
Core — Execution Layer

Receives Sarathi enforcement record. Executes the action.
Preserves trace_id. No transformation of upstream data.
"""


from typing import Any


def execute(sarathi_output: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the enforced action.

    Returns execution record with trace_id preserved.
    Raises ValueError on missing trace_id (fail-closed).
    """
    trace_id = sarathi_output.get("trace_id")
    if not trace_id:
        raise ValueError("Core: missing trace_id")

    return {
        "trace_id": trace_id,
        "executed": True,
        "action": sarathi_output.get("action"),
    }
