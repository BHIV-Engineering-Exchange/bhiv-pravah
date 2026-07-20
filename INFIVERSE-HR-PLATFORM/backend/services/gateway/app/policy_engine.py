"""Policy registry, evaluation, and override runtime."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.lineage_envelope import LineageEnvelope
from app.workforce_common import POLICY_AUDIT_EVENT, new_correlation_id, serialize_doc, tenant_id_for_scope, write_workforce_audit

EXAMPLE_POLICIES = [
    {"policy_key": "leave_policy", "name": "Leave Policy", "description": "Leave eligibility observation", "rules": {"min_tenure_days": 90, "effect": "observe"}},
    {"policy_key": "visibility_policy", "name": "Visibility Policy", "description": "Scope-bound visibility", "rules": {"require_scope_match": True, "effect": "allow"}},
    {"policy_key": "growth_policy", "name": "Growth Policy", "description": "Growth signal bounds", "rules": {"allow_derived_signals": True, "effect": "observe"}},
    {"policy_key": "approval_policy", "name": "Approval Policy", "description": "Explicit approval required", "rules": {"require_explicit_approval": True, "effect": "deny_until_approved"}},
    {"policy_key": "retention_policy", "name": "Retention Policy", "description": "Retention boundaries", "rules": {"retention_days": 365, "effect": "allow"}},
]


class PolicyDefinitionCreate(BaseModel):
    policy_key: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    rules: Dict[str, Any] = Field(default_factory=dict)
    scope_type: str = "tenant"


class PolicyEvaluateRequest(BaseModel):
    policy_key: str
    context: Dict[str, Any] = Field(default_factory=dict)
    employee_id: Optional[str] = None
    organization_id: Optional[str] = None


class PolicyOverrideCreate(BaseModel):
    policy_key: str
    evaluation_id: Optional[str] = None
    reason: str
    override_effect: str = "allow"


def _evaluate_rules(policy_key: str, rules: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    effect = rules.get("effect", "observe")
    if policy_key == "leave_policy" and int(context.get("tenure_days", 0)) < int(rules.get("min_tenure_days", 90)):
        return {"decision": "deny", "effect": effect, "rationale": "Tenure below minimum"}
    if policy_key == "visibility_policy" and rules.get("require_scope_match") and not context.get("scope_match", True):
        return {"decision": "deny", "effect": "deny", "rationale": "Scope mismatch"}
    if policy_key == "approval_policy" and rules.get("require_explicit_approval") and not context.get("approved"):
        return {"decision": "deny", "effect": effect, "rationale": "Explicit approval required"}
    return {"decision": "allow" if effect in ("allow", "observe") else "observe", "effect": effect, "rationale": f"policy={policy_key}"}


async def seed_policy_registry(db, scope):
    tenant_id = tenant_id_for_scope(scope)
    seeded = []
    for p in EXAMPLE_POLICIES:
        if await db.policy_definitions.find_one({"policy_key": p["policy_key"], "tenant_id": tenant_id, "version": "1.0.0"}):
            seeded.append(p["policy_key"])
            continue
        now = datetime.now(timezone.utc)
        await db.policy_definitions.insert_one({**p, "version": "1.0.0", "tenant_id": tenant_id, "scope_type": "tenant", "status": "active", "created_at": now, "updated_at": now})
        seeded.append(p["policy_key"])
    await db.policy_registry.update_one({"tenant_id": tenant_id}, {"$set": {"tenant_id": tenant_id, "policies": seeded, "updated_at": datetime.now(timezone.utc)}}, upsert=True)
    return {"seeded": seeded, "tenant_id": tenant_id}


async def list_policy_definitions(db, scope, limit=50):
    q = {} if scope.get("scope") == "platform" else {"tenant_id": tenant_id_for_scope(scope)}
    docs = await db.policy_definitions.find(q).sort("policy_key", 1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def create_policy_definition(db, body: PolicyDefinitionCreate, scope):
    now = datetime.now(timezone.utc)
    doc = {**body.model_dump(), "tenant_id": tenant_id_for_scope(scope), "status": "active", "created_at": now, "updated_at": now}
    result = await db.policy_definitions.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_doc(doc)


async def evaluate_policy(db, body: PolicyEvaluateRequest, scope, correlation_id=None):
    tenant_id = tenant_id_for_scope(scope)
    q = {"policy_key": body.policy_key, "status": "active"}
    if scope.get("scope") != "platform":
        q["tenant_id"] = tenant_id
    policy = await db.policy_definitions.find_one(q)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy definition not found")
    result = _evaluate_rules(body.policy_key, policy.get("rules", {}), body.context)
    cid = correlation_id or new_correlation_id()
    eval_id = f"peval-{uuid.uuid4().hex[:12]}"
    eval_doc = {
        "evaluation_id": eval_id,
        "policy_key": body.policy_key,
        "policy_id": str(policy["_id"]),
        "tenant_id": tenant_id,
        "resolved_scope": {"tenant_id": tenant_id, "organization_id": body.organization_id, "employee_id": body.employee_id, "policy_scope": scope.get("scope")},
        "inputs": body.context,
        "result": result,
        "correlation_id": cid,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
        "created_at": datetime.now(timezone.utc),
    }
    await db.policy_evaluations.insert_one(eval_doc)
    await write_workforce_audit(db, action="policy_evaluate", outcome=result["decision"], scope=scope, correlation_id=cid, context={"evaluation_id": eval_id}, event_type=POLICY_AUDIT_EVENT)
    return {"evaluation_id": eval_id, "policy_key": body.policy_key, "result": result, "correlation_id": cid}


async def create_policy_override(db, body: PolicyOverrideCreate, scope, correlation_id=None):
    cid = correlation_id or new_correlation_id()
    override_id = f"povr-{uuid.uuid4().hex[:12]}"
    doc = {
        "override_id": override_id,
        "policy_key": body.policy_key,
        "evaluation_id": body.evaluation_id,
        "tenant_id": tenant_id_for_scope(scope),
        "reason": body.reason,
        "override_effect": body.override_effect,
        "actor": {"user_id": scope.get("user_id"), "role": scope.get("role")},
        "correlation_id": cid,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
        "created_at": datetime.now(timezone.utc),
    }
    await db.policy_overrides.insert_one(doc)
    await write_workforce_audit(db, action="policy_override", outcome="recorded", scope=scope, correlation_id=cid, context={"override_id": override_id}, event_type=POLICY_AUDIT_EVENT)
    return serialize_doc(doc)
