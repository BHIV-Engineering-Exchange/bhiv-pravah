"""Federated workforce runtime: organizations, hierarchy, and employees."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.lineage_envelope import LineageEnvelope
from app.workforce_common import (
    LIFECYCLE_STATES,
    WORKFORCE_TYPES,
    RUNTIME_AUDIT_EVENT_TYPES,
    compute_inherited_roles,
    doc_id_filter,
    new_correlation_id,
    serialize_doc,
    tenant_id_for_scope,
    workforce_scope_filter,
    write_workforce_audit,
)


class TeamStructure(BaseModel):
    team_id: str
    name: str
    lead_role: Optional[str] = None


class OrganizationCreate(BaseModel):
    name: str
    code: str
    parent_organization_id: Optional[str] = None
    default_roles: List[str] = Field(default_factory=list)
    status: str = "active"


class DivisionCreate(BaseModel):
    organization_id: str
    name: str
    code: str
    status: str = "active"


class UnitCreate(BaseModel):
    division_id: str
    name: str
    code: str
    status: str = "active"


class DepartmentCreate(BaseModel):
    organization_id: str
    unit_id: Optional[str] = None
    name: str
    code: str
    teams: List[TeamStructure] = Field(default_factory=list)
    default_roles: List[str] = Field(default_factory=list)
    status: str = "active"


class EmployeeCreate(BaseModel):
    organization_id: str
    department_id: Optional[str] = None
    unit_id: Optional[str] = None
    workforce_type: str
    role: str
    display_name: str
    email: Optional[str] = None
    lifecycle_state: str = "draft"
    local_system_id: Optional[str] = None
    source_system: str = "sampada"


def _validate_workforce_type(value: str) -> None:
    if value not in WORKFORCE_TYPES:
        raise HTTPException(status_code=422, detail=f"workforce_type must be one of: {sorted(WORKFORCE_TYPES)}")


def _validate_lifecycle(value: str) -> None:
    if value not in LIFECYCLE_STATES:
        raise HTTPException(status_code=422, detail=f"lifecycle_state must be one of: {sorted(LIFECYCLE_STATES)}")


async def _get_org(db, org_id: str, scope: Dict[str, Any]) -> Dict[str, Any]:
    doc = await db.organizations.find_one({**doc_id_filter(org_id), **workforce_scope_filter(scope)})
    if not doc:
        raise HTTPException(status_code=404, detail="Organization not found")
    return doc


async def create_organization(db, body: OrganizationCreate, scope, correlation_id=None):
    cid = correlation_id or new_correlation_id()
    tenant_id = tenant_id_for_scope(scope)
    now = datetime.now(timezone.utc)
    doc = {
        "name": body.name,
        "code": body.code,
        "parent_organization_id": body.parent_organization_id,
        "default_roles": body.default_roles,
        "status": body.status,
        "tenant_id": tenant_id,
        "created_at": now,
        "updated_at": now,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
    }
    result = await db.organizations.insert_one(doc)
    doc["_id"] = result.inserted_id
    await write_workforce_audit(db, action="organization_create", outcome="success", scope=scope, correlation_id=cid, context={"organization_id": str(result.inserted_id)})
    return serialize_doc(doc)


async def list_organizations(db, scope, limit=50):
    docs = await db.organizations.find(workforce_scope_filter(scope)).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def get_organization(db, org_id, scope):
    return serialize_doc(await _get_org(db, org_id, scope))


async def create_division(db, body: DivisionCreate, scope, correlation_id=None):
    await _get_org(db, body.organization_id, scope)
    cid = correlation_id or new_correlation_id()
    now = datetime.now(timezone.utc)
    doc = {
        "organization_id": body.organization_id,
        "name": body.name,
        "code": body.code,
        "status": body.status,
        "tenant_id": tenant_id_for_scope(scope),
        "created_at": now,
        "updated_at": now,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
    }
    result = await db.divisions.insert_one(doc)
    doc["_id"] = result.inserted_id
    await write_workforce_audit(db, action="division_create", outcome="success", scope=scope, correlation_id=cid)
    return serialize_doc(doc)


async def list_divisions(db, scope, organization_id=None, limit=50):
    q = workforce_scope_filter(scope)
    if organization_id:
        q["organization_id"] = organization_id
    docs = await db.divisions.find(q).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def create_unit(db, body: UnitCreate, scope, correlation_id=None):
    if not await db.divisions.find_one({**doc_id_filter(body.division_id), **workforce_scope_filter(scope)}):
        raise HTTPException(status_code=404, detail="Division not found")
    cid = correlation_id or new_correlation_id()
    now = datetime.now(timezone.utc)
    doc = {
        "division_id": body.division_id,
        "name": body.name,
        "code": body.code,
        "status": body.status,
        "tenant_id": tenant_id_for_scope(scope),
        "created_at": now,
        "updated_at": now,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
    }
    result = await db.units.insert_one(doc)
    doc["_id"] = result.inserted_id
    await write_workforce_audit(db, action="unit_create", outcome="success", scope=scope, correlation_id=cid)
    return serialize_doc(doc)


async def list_units(db, scope, division_id=None, limit=50):
    q = workforce_scope_filter(scope)
    if division_id:
        q["division_id"] = division_id
    docs = await db.units.find(q).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def create_department(db, body: DepartmentCreate, scope, correlation_id=None):
    org = await _get_org(db, body.organization_id, scope)
    if body.unit_id and not await db.units.find_one({**doc_id_filter(body.unit_id), **workforce_scope_filter(scope)}):
        raise HTTPException(status_code=404, detail="Unit not found")
    cid = correlation_id or new_correlation_id()
    now = datetime.now(timezone.utc)
    doc = {
        "organization_id": body.organization_id,
        "unit_id": body.unit_id,
        "name": body.name,
        "code": body.code,
        "teams": [t.model_dump() for t in body.teams],
        "default_roles": body.default_roles,
        "status": body.status,
        "tenant_id": tenant_id_for_scope(scope),
        "created_at": now,
        "updated_at": now,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
    }
    result = await db.departments.insert_one(doc)
    doc["_id"] = result.inserted_id
    await write_workforce_audit(db, action="department_create", outcome="success", scope=scope, correlation_id=cid, context={"organization_id": org.get("_id")})
    return serialize_doc(doc)


async def list_departments(db, scope, organization_id=None, limit=50):
    q = workforce_scope_filter(scope)
    if organization_id:
        q["organization_id"] = organization_id
    docs = await db.departments.find(q).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def create_employee(db, body: EmployeeCreate, scope, correlation_id=None):
    _validate_workforce_type(body.workforce_type)
    _validate_lifecycle(body.lifecycle_state)
    org = await _get_org(db, body.organization_id, scope)
    dept_roles: List[str] = []
    if body.department_id:
        dept = await db.departments.find_one({**doc_id_filter(body.department_id), **workforce_scope_filter(scope)})
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        dept_roles = list(dept.get("default_roles") or [])
    cid = correlation_id or new_correlation_id()
    inherited = compute_inherited_roles(body.role, dept_roles, org.get("default_roles"))
    now = datetime.now(timezone.utc)
    workforce_ref_id = f"wf-{uuid.uuid4().hex[:12]}"
    doc = {
        "workforce_ref_id": workforce_ref_id,
        "organization_id": body.organization_id,
        "department_id": body.department_id,
        "unit_id": body.unit_id,
        "workforce_type": body.workforce_type,
        "role": body.role,
        "inherited_roles": inherited,
        "display_name": body.display_name,
        "email": body.email,
        "lifecycle_state": body.lifecycle_state,
        "local_system_id": body.local_system_id,
        "source_system": body.source_system,
        "tenant_id": tenant_id_for_scope(scope),
        "created_at": now,
        "updated_at": now,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
    }
    result = await db.employees.insert_one(doc)
    doc["_id"] = result.inserted_id
    await write_workforce_audit(db, action="employee_create", outcome="success", scope=scope, correlation_id=cid, context={"employee_id": str(result.inserted_id), "workforce_ref_id": workforce_ref_id})
    return serialize_doc(doc)


async def list_employees(db, scope, organization_id=None, department_id=None, workforce_type=None, limit=50):
    q = workforce_scope_filter(scope)
    if organization_id:
        q["organization_id"] = organization_id
    if department_id:
        q["department_id"] = department_id
    if workforce_type:
        q["workforce_type"] = workforce_type
    docs = await db.employees.find(q).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def get_employee(db, employee_id, scope):
    doc = await db.employees.find_one({**doc_id_filter(employee_id), **workforce_scope_filter(scope)})
    if not doc:
        raise HTTPException(status_code=404, detail="Employee not found")
    return serialize_doc(doc)


async def get_org_hierarchy(db, organization_id, scope):
    org = await get_organization(db, organization_id, scope)
    org_oid = org["id"]
    divisions = await list_divisions(db, scope, organization_id=org_oid)
    units = []
    for div in divisions:
        units.extend(await list_units(db, scope, division_id=div["id"]))
    return {
        "organization": org,
        "divisions": divisions,
        "units": units,
        "departments": await list_departments(db, scope, organization_id=org_oid),
        "employees": await list_employees(db, scope, organization_id=org_oid, limit=200),
        "policy_scope": scope,
    }


async def workforce_trace_replay(db, scope, correlation_id=None, limit=30):
    filt: Dict[str, Any] = {"event_type": {"$in": list(RUNTIME_AUDIT_EVENT_TYPES)}}
    if scope.get("scope") != "platform":
        user_id = str(scope.get("user_id") or "")
        filt["$or"] = [
            {"actor.user_id": user_id},
            {"context.scope_label": scope.get("scope_label")},
        ]
    if correlation_id:
        filt["correlation_id"] = correlation_id
    events = await db.audit_logs.find(filt).sort("created_at", -1).limit(limit).to_list(limit)
    events.reverse()
    return {
        "correlation_id": correlation_id or (events[-1].get("correlation_id") if events else None),
        "event_count": len(events),
        "events": [
            {
                "action": e.get("action"),
                "outcome": e.get("outcome"),
                "correlation_id": e.get("correlation_id"),
                "trace_id": e.get("trace_id"),
                "created_at": str(e.get("created_at")),
            }
            for e in events
        ],
        "policy_scope": scope,
    }
