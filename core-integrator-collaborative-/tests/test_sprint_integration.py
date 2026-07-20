"""Integration tests for sprint deliverables across packages."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import bhiv_bucket
from integration_bridge import ArtifactGraph
from src.utils.determinism import compute_pipeline_deterministic_hash, strip_volatile


class TestBucketArtifactTypes:
    def test_telemetry_and_alert_types_registered(self):
        assert "telemetry" in bhiv_bucket.ARTIFACT_TYPES
        assert "alert" in bhiv_bucket.ARTIFACT_TYPES
        assert bhiv_bucket.ARTIFACT_TYPES.index("telemetry") < bhiv_bucket.ARTIFACT_TYPES.index("instruction")
        assert bhiv_bucket.ARTIFACT_TYPES.index("alert") > bhiv_bucket.ARTIFACT_TYPES.index("result")


class TestArtifactGraphMapping:
    def test_telemetry_and_alert_numbers(self):
        graph = ArtifactGraph(bucket_url="http://127.0.0.1:8005")
        assert graph._get_artifact_number("telemetry") == 0
        assert graph._get_artifact_number("alert") == 5
        assert graph._get_artifact_number("instruction") == 1
        assert graph._get_artifact_number("result") == 4


class TestDeterminismWithSignal:
    def test_signal_volatile_fields_stripped(self):
        signal = {
            "metric": "transformer_temp_c",
            "value": 97.5,
            "classification": "critical",
            "derived_at": "2026-07-08T10:00:00Z",
            "signal_id": "sig_abc",
        }
        stripped = strip_volatile(signal)
        assert "derived_at" not in stripped
        assert "signal_id" not in stripped
        assert stripped["classification"] == "critical"

    def test_hash_stable_when_only_volatile_signal_fields_change(self):
        instruction = {"prompt": "test", "intent": "generate", "module": "creator"}
        blueprint = {"target_product": "creator", "intent_type": "generate", "payload": {"x": 1}}
        contract = {"execution_plan": ["a"], "constraints": {}}
        execution = {"status": "success", "message": "ok", "result": {"out": 1}}
        signal_a = {
            "metric": "transformer_temp_c",
            "value": 97.5,
            "classification": "critical",
            "derived_at": "2026-07-08T10:00:00Z",
            "signal_id": "sig_a",
        }
        signal_b = {**signal_a, "derived_at": "2026-07-08T11:00:00Z", "signal_id": "sig_b"}
        hash_a = compute_pipeline_deterministic_hash(instruction, blueprint, contract, execution, signal_a)
        hash_b = compute_pipeline_deterministic_hash(instruction, blueprint, contract, execution, signal_b)
        assert hash_a == hash_b

    def test_hash_changes_when_signal_classification_changes(self):
        instruction = {"prompt": "test"}
        blueprint = {}
        contract = {}
        execution = {}
        signal_nominal = {"metric": "voltage_v", "value": 230, "classification": "nominal"}
        signal_critical = {"metric": "voltage_v", "value": 230, "classification": "critical"}
        h1 = compute_pipeline_deterministic_hash(instruction, blueprint, contract, execution, signal_nominal)
        h2 = compute_pipeline_deterministic_hash(instruction, blueprint, contract, execution, signal_critical)
        assert h1 != h2


class TestServicesConfigSprint:
    def test_services_yml_lists_ten_services(self):
        from config import ConfigManager

        services = ConfigManager.get_config()["services"]
        expected = {
            "prompt_runner",
            "creator_core",
            "bhiv_core",
            "integration_bridge",
            "bucket",
            "cet",
            "sarathi",
            "gate",
            "control_plane",
            "telemetry",
        }
        assert expected.issubset(set(services.keys()))

    def test_control_plane_depends_on_telemetry(self):
        from config import ConfigManager

        deps = ConfigManager.get_service_dependencies("control_plane")
        assert "telemetry" in deps
        assert "integration_bridge" in deps
