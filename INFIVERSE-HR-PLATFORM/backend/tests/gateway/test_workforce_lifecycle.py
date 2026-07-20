"""Lifecycle transition validation tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).resolve().parents[2] / "services" / "gateway"
if str(GATEWAY_ROOT) not in sys.path:
    sys.path.insert(0, str(GATEWAY_ROOT))

from app.workforce_lifecycle import ALLOWED_TRANSITIONS  # noqa: E402
from app.workforce_common import LIFECYCLE_STATES  # noqa: E402

pytestmark = pytest.mark.e2e_unit


def test_all_lifecycle_states_defined():
    for state in LIFECYCLE_STATES:
        assert state in ALLOWED_TRANSITIONS


def test_offboarded_terminal():
    assert ALLOWED_TRANSITIONS["offboarded"] == frozenset()


def test_active_can_offboard_prep():
    assert "offboarding_prep" in ALLOWED_TRANSITIONS["active"]
