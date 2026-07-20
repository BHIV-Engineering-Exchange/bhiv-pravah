"""Signal generation stage for telemetry events."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.utils.insightflow import make_lineage_event
from src.utils.telemetry_writer import emit_insightflow_event

THRESHOLDS_PATH = Path(__file__).resolve().parent / "thresholds.json"


def _load_thresholds() -> dict:
    return json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))


def _classify(metric: str, value: float) -> tuple[str, bool]:
    thresholds = _load_thresholds().get(metric, {"warning": 9999999.0, "critical": 9999999.0})
    if value >= thresholds["critical"]:
        return "critical", True
    if value >= thresholds["warning"]:
        return "warning", True
    return "nominal", False


def generate_signal(telemetry_event: dict) -> dict:
    """Generate signal and synthesized prompt from telemetry event."""
    trace_id = telemetry_event["trace_id"]
    classification, breached = _classify(telemetry_event["metric"], float(telemetry_event["value"]))
    signal = {
        "signal_id": f"sig_{uuid.uuid4().hex[:12]}",
        "trace_id": trace_id,
        "metric": telemetry_event["metric"],
        "value": telemetry_event["value"],
        "unit": telemetry_event["unit"],
        "classification": classification,
        "threshold_breached": breached,
        "derived_at": datetime.now(timezone.utc).isoformat(),
        "source_module_id": "signal_generator",
        "status": "success",
    }
    signal["prompt"] = (
        f"Evaluate grid response for {signal['metric']} reading of "
        f"{signal['value']}{signal['unit']} at {telemetry_event['source_id']}, "
        f"classified {signal['classification']}."
    )
    emit_insightflow_event(
        make_lineage_event(
            "signal.generated",
            instruction_id=trace_id,
            execution_id=signal["signal_id"],
            component="signal_generator",
            status="success",
            details={"trace_id": trace_id, "classification": classification},
        )
    )
    return signal
