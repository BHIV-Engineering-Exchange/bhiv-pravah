"""Integration tests for control_plane_service dashboard APIs."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_ENABLED", "false")

import control_plane_service as cp


@pytest.fixture
def client():
    return TestClient(cp.app, raise_server_exceptions=False)


@pytest.fixture
def mock_runtime_status():
    return {
        "generated_at": "2026-07-08T10:00:00+00:00",
        "services": {
            "telemetry": {"status": "healthy", "pid": 1, "port": 8010, "restarts": 0, "last_restart_at": None},
            "control_plane": {"status": "healthy", "pid": 2, "port": 8009, "restarts": 0, "last_restart_at": None},
        },
        "uptime_seconds": 120.0,
        "shutting_down": False,
    }


class TestControlPlaneEndpoints:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "control_plane"

    @patch.object(cp, "read_status")
    @patch.object(cp, "_alerts_from_bucket", return_value=[])
    @patch.object(cp, "_collect_service_metrics", return_value={})
    @patch.object(cp, "_safe_get_json", return_value={"failed_replays": 0})
    def test_metrics_shape(self, _replay, _svc_metrics, _alerts, mock_status, client, mock_runtime_status):
        mock_status.return_value = mock_runtime_status
        resp = client.get("/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert "active_services" in body
        assert "request_throughput_req_min" in body
        assert "error_rate_pct" in body
        assert "latency_ms" in body
        assert "system_uptime_seconds" in body

    @patch.object(cp, "read_status")
    @patch.object(cp, "_alerts_from_bucket", return_value=[{"alert_id": "a1"}])
    def test_system_status_ok(self, _alerts, mock_status, client, mock_runtime_status):
        mock_status.return_value = mock_runtime_status
        resp = client.get("/system/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["overall_status"] == "ok"
        assert body["active_alerts"] == 1
        assert "telemetry" in body["services"]

    @patch.object(cp, "read_status")
    @patch.object(cp, "_alerts_from_bucket", return_value=[])
    def test_system_status_degraded_on_crash_loop(self, _alerts, mock_status, client, mock_runtime_status):
        mock_runtime_status["services"]["telemetry"]["status"] = "CRASH_LOOPING"
        mock_status.return_value = mock_runtime_status
        body = client.get("/system/status").json()
        assert body["overall_status"] == "degraded"

    @patch.object(cp, "_safe_get_json")
    @patch.object(cp, "_alerts_from_bucket", return_value=[{"severity": "critical"}, {"severity": "critical"}])
    @patch.object(cp, "read_status")
    def test_dashboard_executive(self, mock_status, _alerts, mock_bucket, client, mock_runtime_status):
        mock_status.return_value = mock_runtime_status
        mock_bucket.return_value = {"bucket": {"total_traces": 42}}
        resp = client.get("/dashboard/executive")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_pipeline_executions_today"] == 42
        assert body["active_alerts_by_severity"]["critical"] == 2
        assert body["overall_system_status"] == "ok"

    @patch.object(cp, "read_status")
    def test_dashboard_runtime(self, mock_status, client, mock_runtime_status):
        mock_status.return_value = mock_runtime_status
        body = client.get("/dashboard/runtime").json()
        assert body["uptime_seconds"] == 120.0
        assert body["services"]["telemetry"]["status"] == "healthy"

    @patch.object(cp, "get_alert_ring_buffer", return_value=[])
    @patch.object(cp, "_alerts_from_bucket")
    def test_dashboard_alerts_sorted_newest_first(self, mock_bucket_alerts, _cache, client):
        mock_bucket_alerts.return_value = [
            {"alert_id": "old", "raised_at": "2026-07-08T09:00:00Z"},
            {"alert_id": "new", "raised_at": "2026-07-08T10:00:00Z"},
        ]
        alerts = client.get("/dashboard/alerts").json()["alerts"]
        assert alerts[0]["alert_id"] == "new"

    @patch.object(cp, "_safe_get_json")
    def test_dashboard_telemetry_classification_breakdown(self, mock_get, client):
        mock_get.side_effect = [
            {"traces": [{"trace_id": "trace_1"}]},
            {
                "artifacts": [
                    {"artifact_type": "telemetry", "data": {"timestamp": "2026-07-08T10:00:00Z"}},
                    {
                        "artifact_type": "alert",
                        "data": {
                            "signal": {"classification": "critical"},
                        },
                    },
                ]
            },
        ]
        body = client.get("/dashboard/telemetry").json()
        assert len(body["recent_telemetry"]) == 1
        assert body["classification_breakdown"]["critical"] == 1
