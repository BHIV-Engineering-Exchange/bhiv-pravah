"""Integration tests for telemetry_service ingest flow."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("AUTH_API_KEY", "")

import telemetry_service as ts


@pytest.fixture
def client():
    return TestClient(ts.app, raise_server_exceptions=False)


class TestTelemetryService:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "telemetry"

    def test_ingest_rejects_invalid_payload(self, client):
        resp = client.post("/telemetry/ingest", json={"source_id": "x"})
        assert resp.status_code == 422

    @patch("telemetry_service.requests.post")
    @patch("telemetry_service.generate_signal")
    @patch("telemetry_service.generate_alert", return_value=None)
    def test_ingest_success_minimal_chain(self, _alert, mock_signal, mock_post, client):
        mock_signal.return_value = {
            "signal_id": "sig_test",
            "trace_id": "trace_test",
            "prompt": "Evaluate grid response",
            "classification": "nominal",
        }
        store_resp = MagicMock()
        store_resp.raise_for_status.return_value = None
        store_resp.status_code = 200
        pipeline_resp = MagicMock()
        pipeline_resp.raise_for_status.return_value = None
        pipeline_resp.json.return_value = {"status": "success", "pipeline_result": {}}
        mock_post.side_effect = [store_resp, pipeline_resp]

        payload = {
            "source_id": "substation-7",
            "metric": "transformer_temp_c",
            "value": 72.0,
            "unit": "celsius",
            "timestamp": "2026-07-08T10:00:00Z",
        }
        resp = client.post("/telemetry/ingest", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["trace_id"].startswith("trace_")
        assert body["signal"]["classification"] == "nominal"
        assert mock_post.call_count == 2

    def test_metrics_snapshot_endpoint(self, client):
        resp = client.get("/internal/metrics-snapshot")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_requests" in body
        assert "latency_ms" in body
