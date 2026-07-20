"""Live WO/GE/SETU Sprint additive gap-fix tests (offline).

Covers, without modifying any existing assertions:
- Gap Fix #1: role-move with transition_type="promotion" emits the dedicated
  `employee_promotion` audit action (and a lateral move keeps `employee_role_move`).
- Gap Fix #2: the lineage envelope includes `schema_version`.

The async behavior test uses asyncio.run() over an in-memory async Mongo
(mongomock_motor); it is skipped gracefully if that optional package is absent,
so it never breaks the existing baseline suite.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).resolve().parents[2] / "services" / "gateway"
if str(GATEWAY_ROOT) not in sys.path:
    sys.path.insert(0, str(GATEWAY_ROOT))

from app.lineage_envelope import LineageEnvelope  # noqa: E402
from app.workforce_lifecycle import LifecycleTransition, role_movement  # noqa: E402

pytestmark = pytest.mark.e2e_unit

PLATFORM_SCOPE = {"scope": "platform", "scope_label": "platform_admin", "role": "admin", "user_id": None}


def test_transition_type_default_is_role_change():
    assert LifecycleTransition().transition_type == "role_change"


def test_transition_type_accepts_promotion():
    assert LifecycleTransition(new_role="manager", transition_type="promotion").transition_type == "promotion"


def test_lineage_envelope_includes_schema_version():
    payload = LineageEnvelope.from_request(correlation_id="cid-x").to_dict()
    assert "schema_version" in payload
    assert payload["schema_version"] == "1.0.0"


def _run_role_move(transition_type):
    mongomock_motor = pytest.importorskip("mongomock_motor")
    client = mongomock_motor.AsyncMongoMockClient()
    db = client["bhiv_hr_test"]

    async def scenario():
        await db.employees.insert_one({"id": "emp-t21", "lifecycle_state": "active", "role": "analyst", "tenant_id": "platform"})
        body = LifecycleTransition(new_role="operations_manager", transition_type=transition_type, reason="t21")
        await role_movement(db, "emp-t21", PLATFORM_SCOPE, body, correlation_id="cid-t21")
        emp = await db.employees.find_one({"id": "emp-t21"})
        audits = await db.audit_logs.find({"correlation_id": "cid-t21"}).to_list(10)
        return emp, audits

    return asyncio.run(scenario())


def test_promotion_emits_employee_promotion_audit():
    emp, audits = _run_role_move("promotion")
    actions = {a.get("action") for a in audits}
    assert "employee_promotion" in actions
    assert "employee_role_move" not in actions
    assert emp.get("transition_type") == "promotion"
    assert emp.get("role") == "operations_manager"


def test_lateral_move_keeps_employee_role_move_audit():
    _, audits = _run_role_move("lateral")
    actions = {a.get("action") for a in audits}
    assert "employee_role_move" in actions
    assert "employee_promotion" not in actions
