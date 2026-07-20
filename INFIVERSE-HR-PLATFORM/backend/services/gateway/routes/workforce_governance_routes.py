"""Workforce, policy, governance, and SETU participation API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request

from app.database import get_mongo_db
from app.decision_ledger import DecisionCreate, create_decision, get_decision, list_decisions, record_decision_from_review, replay_decisions
from app.decision_workflow import (
    ChallengeCreate,
    ReviewComplete,
    ReviewCreate,
    WorkflowOverrideCreate,
    apply_workflow_override,
    assign_review,
    complete_review,
    create_challenge,
    list_challenges,
    record_workflow_override,
)
from app.policy_engine import PolicyDefinitionCreate, PolicyEvaluateRequest, PolicyOverrideCreate, create_policy_definition, create_policy_override, evaluate_policy, list_policy_definitions, seed_policy_registry
from app.setu_participation import SetuSignalIngest, ingest_setu_signal, list_setu_signals, setu_trace_continuity
from app.workforce_common import assert_workforce_access
from app.workforce_lifecycle import LifecycleTransition, complete_onboarding, department_transfer, offboarding_prepare, onboard_employee, role_movement, status_change
from app.workforce_runtime import (
    DepartmentCreate,
    DivisionCreate,
    EmployeeCreate,
    OrganizationCreate,
    UnitCreate,
    create_department,
    create_division,
    create_employee,
    create_organization,
    create_unit,
    get_employee,
    get_org_hierarchy,
    get_organization,
    list_departments,
    list_divisions,
    list_employees,
    list_organizations,
    list_units,
    workforce_trace_replay,
)
from jwt_auth import get_auth

router = APIRouter(tags=["Workforce Governance"])


def _correlation_id(request: Request) -> Optional[str]:
    return getattr(request.state, "correlation_id", None)


@router.post("/v1/workforce/organizations")
async def api_create_organization(body: OrganizationCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_organization(db, body, scope, _correlation_id(request))


@router.get("/v1/workforce/organizations")
async def api_list_organizations(auth=Depends(get_auth), limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_organizations(db, scope, limit), "policy_scope": scope}


@router.get("/v1/workforce/organizations/{org_id}")
async def api_get_organization(org_id: str, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await get_organization(db, org_id, scope)


@router.get("/v1/workforce/organizations/{org_id}/hierarchy")
async def api_org_hierarchy(org_id: str, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await get_org_hierarchy(db, org_id, scope)


@router.post("/v1/workforce/divisions")
async def api_create_division(body: DivisionCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_division(db, body, scope, _correlation_id(request))


@router.get("/v1/workforce/divisions")
async def api_list_divisions(auth=Depends(get_auth), organization_id: Optional[str] = None, limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_divisions(db, scope, organization_id, limit), "policy_scope": scope}


@router.post("/v1/workforce/units")
async def api_create_unit(body: UnitCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_unit(db, body, scope, _correlation_id(request))


@router.get("/v1/workforce/units")
async def api_list_units(auth=Depends(get_auth), division_id: Optional[str] = None, limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_units(db, scope, division_id, limit), "policy_scope": scope}


@router.post("/v1/workforce/departments")
async def api_create_department(body: DepartmentCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_department(db, body, scope, _correlation_id(request))


@router.get("/v1/workforce/departments")
async def api_list_departments(auth=Depends(get_auth), organization_id: Optional[str] = None, limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_departments(db, scope, organization_id, limit), "policy_scope": scope}


@router.post("/v1/workforce/employees")
async def api_create_employee(body: EmployeeCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_employee(db, body, scope, _correlation_id(request))


@router.get("/v1/workforce/employees")
async def api_list_employees(
    auth=Depends(get_auth),
    organization_id: Optional[str] = None,
    department_id: Optional[str] = None,
    workforce_type: Optional[str] = None,
    limit: int = 50,
):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_employees(db, scope, organization_id, department_id, workforce_type, limit), "policy_scope": scope}


@router.get("/v1/workforce/employees/{employee_id}")
async def api_get_employee(employee_id: str, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await get_employee(db, employee_id, scope)


@router.get("/v1/workforce/trace-replay")
async def api_workforce_trace_replay(auth=Depends(get_auth), correlation_id: Optional[str] = None, limit: int = 30):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await workforce_trace_replay(db, scope, correlation_id, limit)


@router.post("/v1/workforce/employees/{employee_id}/lifecycle/onboard")
async def api_onboard(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await onboard_employee(db, employee_id, scope, body, _correlation_id(request))


@router.post("/v1/workforce/employees/{employee_id}/lifecycle/onboard-complete")
async def api_onboard_complete(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await complete_onboarding(db, employee_id, scope, body, _correlation_id(request))


@router.post("/v1/workforce/employees/{employee_id}/lifecycle/role-move")
async def api_role_move(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await role_movement(db, employee_id, scope, body, _correlation_id(request))


@router.post("/v1/workforce/employees/{employee_id}/lifecycle/department-transfer")
async def api_dept_transfer(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await department_transfer(db, employee_id, scope, body, _correlation_id(request))


@router.patch("/v1/workforce/employees/{employee_id}/lifecycle/status")
async def api_status_change(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await status_change(db, employee_id, scope, body, _correlation_id(request))


@router.post("/v1/workforce/employees/{employee_id}/lifecycle/offboard-prepare")
async def api_offboard_prepare(employee_id: str, body: LifecycleTransition, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await offboarding_prepare(db, employee_id, scope, body, _correlation_id(request))


@router.post("/v1/policies/seed")
async def api_seed_policies(auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await seed_policy_registry(db, scope)


@router.get("/v1/policies/definitions")
async def api_list_policies(auth=Depends(get_auth), limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_policy_definitions(db, scope, limit), "policy_scope": scope}


@router.post("/v1/policies/definitions")
async def api_create_policy(body: PolicyDefinitionCreate, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_policy_definition(db, body, scope)


@router.post("/v1/policies/evaluate")
async def api_evaluate_policy(body: PolicyEvaluateRequest, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await evaluate_policy(db, body, scope, _correlation_id(request))


@router.post("/v1/policies/overrides")
async def api_policy_override(body: PolicyOverrideCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_policy_override(db, body, scope, _correlation_id(request))


@router.post("/v1/governance/challenges")
async def api_create_challenge(body: ChallengeCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_challenge(db, body, scope, _correlation_id(request))


@router.get("/v1/governance/challenges")
async def api_list_challenges(auth=Depends(get_auth), limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_challenges(db, scope, limit), "policy_scope": scope}


@router.post("/v1/governance/reviews")
async def api_assign_review(body: ReviewCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await assign_review(db, body, scope, _correlation_id(request))


@router.post("/v1/governance/reviews/{review_id}/complete")
async def api_complete_review(review_id: str, body: ReviewComplete, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await complete_review(db, review_id, body, scope)


@router.post("/v1/governance/overrides")
async def api_workflow_override(body: WorkflowOverrideCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await record_workflow_override(db, body, scope, _correlation_id(request))


@router.post("/v1/governance/overrides/{override_id}/apply")
async def api_apply_override(override_id: str, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await apply_workflow_override(db, override_id, scope)


@router.post("/v1/decisions")
async def api_create_decision(body: DecisionCreate, request: Request, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await create_decision(db, body, scope, _correlation_id(request))


@router.get("/v1/decisions/replay")
async def api_decision_replay(decision_id: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 50, auth=Depends(get_auth)):
    assert_workforce_access(auth)
    db = await get_mongo_db()
    return await replay_decisions(db, decision_id, correlation_id, limit)


@router.get("/v1/decisions")
async def api_list_decisions(auth=Depends(get_auth), limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_decisions(db, scope, limit), "policy_scope": scope}


@router.get("/v1/decisions/{decision_id}")
async def api_get_decision(decision_id: str, auth=Depends(get_auth)):
    assert_workforce_access(auth)
    db = await get_mongo_db()
    return await get_decision(db, decision_id)


@router.post("/v1/governance/reviews/{review_id}/decision")
async def api_decision_from_review(review_id: str, owner: str, rationale: str, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await record_decision_from_review(db, review_id, owner, rationale, scope)


@router.post("/v1/setu/signals/{signal_type}")
async def api_setu_signal(signal_type: str, body: SetuSignalIngest, auth=Depends(get_auth)):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return await ingest_setu_signal(db, body, scope, signal_type)


@router.get("/v1/setu/signals")
async def api_list_setu_signals(auth=Depends(get_auth), signal_type: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 50):
    scope = assert_workforce_access(auth)
    db = await get_mongo_db()
    return {"items": await list_setu_signals(db, scope, signal_type, correlation_id, limit)}


@router.get("/v1/setu/trace/{trace_id}")
async def api_setu_trace(trace_id: str, auth=Depends(get_auth), limit: int = 50):
    assert_workforce_access(auth)
    db = await get_mongo_db()
    return await setu_trace_continuity(db, trace_id, limit)
