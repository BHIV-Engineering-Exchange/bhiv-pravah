"""Workforce lifecycle state transitions and validation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.lineage_envelope import LineageEnvelope
from app.workforce_common import (
    GOVERNANCE_AUDIT_EVENT,
    LIFECYCLE_STATES,
    compute_inherited_roles,
    doc_id_filter,
    new_correlation_id,
    serialize_doc,
    workforce_scope_filter,
    write_workforce_audit,
)

ALLOWED_TRANSITIONS: Dict[str, frozenset] = {
    "draft": frozenset({"onboarding"}),
    "onboarding": frozenset({"active"}),
    "active": frozenset({"role_change_pending", "transfer_pending", "offboarding_prep", "inactive"}),
    "role_change_pending": frozenset({"active"}),
    "transfer_pending": frozenset({"active"}),
    "offboarding_prep": frozenset({"offboarded", "inactive"}),
    "inactive": frozenset({"active", "onboarding"}),
    "offboarded": frozenset(),
}


class LifecycleTransition(BaseModel):
    target_state: Optional[str] = None
    new_role: Optional[str] = None
    new_department_id: Optional[str] = None
    reason: Optional[str] = None
    transition_type: Optional[str] = "role_change"


async def _transition_employee(db, employee_id, scope, *, action, updates, correlation_id=None, reason=None):
    q = {**doc_id_filter(employee_id), **workforce_scope_filter(scope)}
    doc = await db.employees.find_one(q)
    if not doc:
        raise HTTPException(status_code=404, detail="Employee not found")
    prior_state = doc.get("lifecycle_state")
    new_state = updates.get("lifecycle_state", prior_state)
    if new_state != prior_state:
        allowed = ALLOWED_TRANSITIONS.get(prior_state, frozenset())
        if new_state not in allowed:
            raise HTTPException(status_code=409, detail=f"Invalid transition from {prior_state} to {new_state}")
    cid = correlation_id or new_correlation_id()
    updates["updated_at"] = datetime.now(timezone.utc)
    updates["lineage"] = LineageEnvelope.from_request(correlation_id=cid).to_dict()
    await db.employees.update_one(q, {"$set": updates})
    updated = await db.employees.find_one(q)
    await write_workforce_audit(
        db,
        action=action,
        outcome="success",
        scope=scope,
        correlation_id=cid,
        detail=reason,
        context={"employee_id": employee_id, "prior_state": prior_state, "new_state": new_state},
        event_type=GOVERNANCE_AUDIT_EVENT,
    )
    return serialize_doc(updated)


async def onboard_employee(db, employee_id, scope, body, correlation_id=None):
    emp_q = {**doc_id_filter(employee_id), **workforce_scope_filter(scope)}
    doc = await db.employees.find_one(emp_q)
    if not doc:
        raise HTTPException(status_code=404, detail="Employee not found")
    if doc.get("lifecycle_state") not in ("draft", "inactive"):
        raise HTTPException(status_code=409, detail="Onboarding only allowed from draft or inactive")
    return await _transition_employee(db, employee_id, scope, action="employee_onboard", updates={"lifecycle_state": "onboarding"}, correlation_id=correlation_id, reason=body.reason)


async def complete_onboarding(db, employee_id, scope, body, correlation_id=None):
    return await _transition_employee(db, employee_id, scope, action="employee_onboard_complete", updates={"lifecycle_state": "active"}, correlation_id=correlation_id, reason=body.reason)


async def role_movement(db, employee_id, scope, body, correlation_id=None):
    if not body.new_role:
        raise HTTPException(status_code=422, detail="new_role is required")
    inherited = compute_inherited_roles(body.new_role)
    transition_type = (body.transition_type or "role_change").lower()
    action = "employee_promotion" if transition_type == "promotion" else "employee_role_move"
    return await _transition_employee(db, employee_id, scope, action=action, updates={"lifecycle_state": "active", "role": body.new_role, "inherited_roles": inherited, "transition_type": transition_type}, correlation_id=correlation_id, reason=body.reason)


async def department_transfer(db, employee_id, scope, body, correlation_id=None):
    if not body.new_department_id:
        raise HTTPException(status_code=422, detail="new_department_id is required")
    if not await db.departments.find_one({**doc_id_filter(body.new_department_id), **workforce_scope_filter(scope)}):
        raise HTTPException(status_code=404, detail="Department not found")
    return await _transition_employee(db, employee_id, scope, action="employee_department_transfer", updates={"lifecycle_state": "active", "department_id": body.new_department_id}, correlation_id=correlation_id, reason=body.reason)


async def status_change(db, employee_id, scope, body, correlation_id=None):
    if not body.target_state or body.target_state not in LIFECYCLE_STATES:
        raise HTTPException(status_code=422, detail="Valid target_state is required")
    return await _transition_employee(db, employee_id, scope, action="employee_status_change", updates={"lifecycle_state": body.target_state}, correlation_id=correlation_id, reason=body.reason)


async def offboarding_prepare(db, employee_id, scope, body, correlation_id=None):
    return await _transition_employee(db, employee_id, scope, action="employee_offboard_prepare", updates={"lifecycle_state": "offboarding_prep"}, correlation_id=correlation_id, reason=body.reason)
