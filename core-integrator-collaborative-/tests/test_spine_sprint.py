"""Unit tests for SHAKTI sprint spine package."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from spine.alert_generator import (
    ALERT_RING_BUFFER,
    generate_alert,
    get_alert_ring_buffer,
    push_alert,
)
from spine.signal_generator import generate_signal
from spine.telemetry_schema import validate_telemetry


class TestTelemetrySchema:
    def test_valid_payload_passes(self):
        payload = {
            "source_id": "substation-7",
            "metric": "transformer_temp_c",
            "value": 72.0,
            "unit": "celsius",
            "timestamp": "2026-07-08T10:00:00Z",
        }
        ok, err = validate_telemetry(payload)
        assert ok is True
        assert err is None

    def test_missing_required_field_fails(self):
        payload = {"source_id": "substation-7", "metric": "transformer_temp_c"}
        ok, err = validate_telemetry(payload)
        assert ok is False
        assert err is not None

    def test_invalid_value_type_fails(self):
        payload = {
            "source_id": "substation-7",
            "metric": "transformer_temp_c",
            "value": "hot",
            "unit": "celsius",
            "timestamp": "2026-07-08T10:00:00Z",
        }
        ok, err = validate_telemetry(payload)
        assert ok is False


class TestSignalGenerator:
    @patch("spine.signal_generator.emit_insightflow_event")
    def test_nominal_classification(self, _mock_emit):
        telemetry = {
            "trace_id": "trace_test001",
            "source_id": "grid-zone-a",
            "metric": "grid_load_mw",
            "value": 420.0,
            "unit": "mw",
            "timestamp": "2026-07-08T10:00:00Z",
        }
        signal = generate_signal(telemetry)
        assert signal["trace_id"] == "trace_test001"
        assert signal["classification"] == "nominal"
        assert signal["threshold_breached"] is False
        assert signal["source_module_id"] == "signal_generator"
        assert "prompt" in signal

    @patch("spine.signal_generator.emit_insightflow_event")
    def test_critical_classification(self, _mock_emit):
        telemetry = {
            "trace_id": "trace_test002",
            "source_id": "substation-7",
            "metric": "transformer_temp_c",
            "value": 97.5,
            "unit": "celsius",
            "timestamp": "2026-07-08T10:00:00Z",
        }
        signal = generate_signal(telemetry)
        assert signal["classification"] == "critical"
        assert signal["threshold_breached"] is True


class TestAlertGenerator:
    def setup_method(self):
        ALERT_RING_BUFFER.clear()

    def _signal(self, classification="critical"):
        return {
            "trace_id": "trace_alert01",
            "metric": "transformer_temp_c",
            "classification": classification,
        }

    def test_no_alert_for_nominal_signal(self):
        pipeline = {"status": "success", "pipeline_result": {}}
        assert generate_alert(self._signal("nominal"), pipeline) is None

    def test_critical_signal_generates_alert(self):
        pipeline = {
            "status": "success",
            "pipeline_result": {
                "gate_decision": {"gate_status": "ALLOWED"},
                "execution_result": {"status": "success"},
            },
        }
        alert = generate_alert(self._signal("critical"), pipeline)
        assert alert is not None
        assert alert["severity"] == "critical"
        assert alert["trace_id"] == "trace_alert01"
        assert alert["signal"]["classification"] == "critical"
        assert alert["decision_summary"]["pipeline_status"] == "success"

    def test_rejected_gate_generates_high_alert(self):
        pipeline = {
            "status": "rejected",
            "pipeline_result": {
                "gate_decision": {"gate_status": "REJECTED"},
                "execution_result": {"status": "success"},
            },
        }
        alert = generate_alert(self._signal("nominal"), pipeline)
        assert alert is not None
        assert alert["severity"] == "high"
        assert "Gate rejected" in alert["reason"]

    def test_ring_buffer_push_and_read(self):
        alert = {"alert_id": "alert_test", "trace_id": "trace_x"}
        push_alert(alert)
        buf = get_alert_ring_buffer()
        assert len(buf) == 1
        assert buf[0]["alert_id"] == "alert_test"
