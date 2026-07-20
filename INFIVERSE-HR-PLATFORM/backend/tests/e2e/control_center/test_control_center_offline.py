"""Offline tests for E2E helpers (no localhost services)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_E2E_ROOT = Path(__file__).resolve().parent
if str(_E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(_E2E_ROOT))

from framework.env_check import check_env_config
from framework.config import E2EConfig
from framework.state_capture import SystemState
from framework.state_compare import compare_states

pytestmark = pytest.mark.e2e_unit


def test_env_check_fails_without_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY_SECRET", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    config = E2EConfig.from_env()
    config.api_key_secret = ""
    result = check_env_config(config)
    assert not result.ok
    assert "API_KEY_SECRET" in result.missing_required[0]


def test_compare_states_detects_audit_increase():
    baseline = SystemState(label="b", captured_at=0.0, audit_events={"count": 2, "events": []})
    final = SystemState(label="f", captured_at=1.0, audit_events={"count": 4, "events": []})
    result = compare_states(baseline, final, require_audit_increase=True)
    assert result.passed
    assert result.deltas["audit_event_count"]["delta"] == 2


def test_compare_states_flags_stat_drop():
    baseline = SystemState(
        label="b",
        captured_at=0.0,
        candidate_stats={"total_candidates": 10, "active_jobs": 2},
    )
    final = SystemState(
        label="f",
        captured_at=1.0,
        candidate_stats={"total_candidates": 5, "active_jobs": 2},
    )
    result = compare_states(baseline, final, require_audit_increase=False)
    assert not result.passed
