"""Unit tests for SHAKTI sprint runtime_manager package."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from runtime_manager.config_validator import (
    RuntimeManagerConfigError,
    validate_services_config,
    validate_startup_order,
)
from runtime_manager.discovery import find_unregistered_service_files, load_declared_services
from runtime_manager.metrics_middleware import get_local_metrics_snapshot
from runtime_manager import state as runtime_state


class TestConfigValidator:
    def test_valid_config_passes(self):
        services = {
            "a": {"port": 8001, "health_check_endpoint": "/health", "depends_on": []},
            "b": {"port": 8002, "health_check_endpoint": "/health", "depends_on": ["a"]},
        }
        validate_services_config(services)

    def test_missing_health_endpoint_raises(self):
        services = {"a": {"port": 8001, "depends_on": []}}
        with pytest.raises(RuntimeManagerConfigError, match="health_check_endpoint"):
            validate_services_config(services)

    def test_undefined_dependency_raises(self):
        services = {
            "a": {"port": 8001, "health_check_endpoint": "/health", "depends_on": ["missing"]},
        }
        with pytest.raises(RuntimeManagerConfigError, match="undefined service"):
            validate_services_config(services)

    def test_port_collision_raises(self):
        services = {
            "a": {"port": 8001, "health_check_endpoint": "/health", "depends_on": []},
            "b": {"port": 8001, "health_check_endpoint": "/health", "depends_on": []},
        }
        with pytest.raises(RuntimeManagerConfigError, match="Port collision"):
            validate_services_config(services)

    def test_validate_startup_order_delegates_to_orchestrator(self):
        orch = MagicMock()
        orch._calculate_startup_order.return_value = ["a", "b"]
        validate_startup_order(orch)
        orch._calculate_startup_order.assert_called_once()


class TestRuntimeState:
    def test_write_and_read_status_roundtrip(self, tmp_path, monkeypatch):
        status_file = tmp_path / "runtime_status.json"
        state_dir = tmp_path
        monkeypatch.setattr(runtime_state, "STATE_DIR", state_dir)
        monkeypatch.setattr(runtime_state, "STATUS_FILE", status_file)

        payload = {
            "services": {"telemetry": {"status": "healthy", "restarts": 0}},
            "uptime_seconds": 12.5,
            "shutting_down": False,
        }
        runtime_state.write_status(payload)
        loaded = runtime_state.read_status()

        assert loaded["services"]["telemetry"]["status"] == "healthy"
        assert loaded["uptime_seconds"] == 12.5
        assert loaded["generated_at"] is not None

    def test_read_status_missing_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr(runtime_state, "STATE_DIR", tmp_path)
        monkeypatch.setattr(runtime_state, "STATUS_FILE", tmp_path / "missing.json")
        defaults = runtime_state.read_status()
        assert defaults["services"] == {}
        assert defaults["shutting_down"] is False


class TestMetricsMiddleware:
    def test_snapshot_has_expected_keys(self):
        snap = get_local_metrics_snapshot()
        assert "total_requests" in snap
        assert "error_rate_pct" in snap
        assert "requests_per_minute" in snap
        assert "latency_ms" in snap
        assert "p50" in snap["latency_ms"]
        assert "p95" in snap["latency_ms"]


class TestDiscovery:
    def test_load_declared_services_includes_sprint_services(self):
        services = load_declared_services()
        assert "telemetry" in services
        assert "control_plane" in services
        assert services["telemetry"]["port"] == 8010
        assert services["control_plane"]["port"] == 8009

    def test_find_unregistered_files_returns_list(self, tmp_path):
        (tmp_path / "custom_service.py").write_text("# stub", encoding="utf-8")
        declared = {"telemetry": {"runner_script": "telemetry_service.py"}}
        found = find_unregistered_service_files(tmp_path, declared)
        assert isinstance(found, list)
        assert "custom_service.py" in found
