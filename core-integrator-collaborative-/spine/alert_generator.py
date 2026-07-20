"""Alert generation and in-memory alert cache."""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Optional

ALERT_RING_BUFFER = deque(maxlen=200)


def get_alert_ring_buffer() -> list:
    return list(ALERT_RING_BUFFER)


def push_alert(alert: dict) -> None:
    ALERT_RING_BUFFER.appendleft(alert)


def generate_alert(signal: dict, pipeline_result: dict) -> Optional[dict]:
    """Generate an alert when critical conditions are met."""
    pipeline_payload = pipeline_result.get("pipeline_result", {}) if isinstance(pipeline_result, dict) else {}
    gate_decision = pipeline_payload.get("gate_decision", {})
    execution_result = pipeline_payload.get("execution_result", {})

    should_alert = (
        signal.get("classification") == "critical"
        or gate_decision.get("gate_status") == "REJECTED"
        or execution_result.get("status") == "error"
    )
    if not should_alert:
        return None

    if signal.get("classification") == "critical":
        severity = "critical"
        reason = f"Critical {signal.get('metric')} reading"
    elif gate_decision.get("gate_status") == "REJECTED":
        severity = "high"
        reason = "Gate rejected execution"
    else:
        severity = "high"
        reason = "Execution returned error"

    alert = {
        "alert_id": f"alert_{uuid.uuid4().hex[:12]}",
        "trace_id": signal["trace_id"],
        "severity": severity,
        "reason": reason,
        "signal": signal,
        "decision_summary": {
            "gate_status": gate_decision.get("gate_status"),
            "execution_status": execution_result.get("status"),
            "pipeline_status": pipeline_result.get("status"),
        },
        "source_module_id": "alert_generator",
        "status": "critical" if severity == "critical" else "error",
        "raised_at": datetime.now(timezone.utc).isoformat(),
    }
    return alert
