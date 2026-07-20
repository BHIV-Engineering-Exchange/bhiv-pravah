"""Challenge, review, and override governance workflows."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.lineage_envelope import LineageEnvelope
from app.workforce_common import GOVERNANCE_AUDIT_EVENT, new_correlation_id, serialize_doc, tenant_id_for_scope, write_workforce_audit


class ChallengeCreate(BaseModel):
    policy_key: str
    evaluation_id: Optional[str] = None
    subject_type: str = "policy_evaluation"
    subject_id: Optional[str] = None
    reason: str


class ReviewCreate(BaseModel):
    challenge_id: str
    reviewer_role: str = "admin"
    notes: Optional[str] = None


class ReviewComplete(BaseModel):
    outcome: str
    notes: Optional[str] = None


class WorkflowOverrideCreate(BaseModel):
    challenge_id: str
    policy_key: str
    reason: str
    override_effect: str = "allow"


async def create_challenge(db, body: ChallengeCreate, scope, correlation_id=None):
    cid = correlation_id or new_correlation_id()
    challenge_id = f"chl-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    doc = {
        "challenge_id": challenge_id,
        "policy_key": body.policy_key,
        "evaluation_id": body.evaluation_id,
        "subject_type": body.subject_type,
        "subject_id": body.subject_id,
        "reason": body.reason,
        "status": "open",
        "tenant_id": tenant_id_for_scope(scope),
        "correlation_id": cid,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
        "created_at": now,
        "updated_at": now,
    }
    await db.challenges.insert_one(doc)
    await write_workforce_audit(db, action="challenge_create", outcome="open", scope=scope, correlation_id=cid, context={"challenge_id": challenge_id}, event_type=GOVERNANCE_AUDIT_EVENT)
    return serialize_doc(doc)


async def list_challenges(db, scope, limit=50) -> List:
    q = {} if scope.get("scope") == "platform" else {"tenant_id": tenant_id_for_scope(scope)}
    docs = await db.challenges.find(q).sort("created_at", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def get_challenge(db, challenge_id: str):
    doc = await db.challenges.find_one({"challenge_id": challenge_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return serialize_doc(doc)


async def assign_review(db, body: ReviewCreate, scope, correlation_id=None):
    ch = await get_challenge(db, body.challenge_id)
    if ch["status"] not in ("open", "under_review"):
        raise HTTPException(status_code=409, detail="Challenge not open for review")
    cid = correlation_id or new_correlation_id()
    review_id = f"rev-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    doc = {
        "review_id": review_id,
        "challenge_id": body.challenge_id,
        "reviewer_role": body.reviewer_role,
        "notes": body.notes,
        "status": "assigned",
        "tenant_id": ch.get("tenant_id"),
        "correlation_id": cid,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
        "created_at": now,
        "updated_at": now,
    }
    await db.reviews.insert_one(doc)
    await db.challenges.update_one({"challenge_id": body.challenge_id}, {"$set": {"status": "under_review", "updated_at": now}})
    await write_workforce_audit(db, action="review_assign", outcome="assigned", scope=scope, correlation_id=cid, context={"review_id": review_id}, event_type=GOVERNANCE_AUDIT_EVENT)
    return serialize_doc(doc)


async def complete_review(db, review_id: str, body: ReviewComplete, scope):
    doc = await db.reviews.find_one({"review_id": review_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Review not found")
    now = datetime.now(timezone.utc)
    await db.reviews.update_one({"review_id": review_id}, {"$set": {"status": "completed", "outcome": body.outcome, "notes": body.notes, "updated_at": now}})
    challenge_status = "resolved" if body.outcome == "upheld" else "rejected"
    await db.challenges.update_one({"challenge_id": doc["challenge_id"]}, {"$set": {"status": challenge_status, "updated_at": now}})
    return serialize_doc(await db.reviews.find_one({"review_id": review_id}))


async def record_workflow_override(db, body: WorkflowOverrideCreate, scope, correlation_id=None):
    ch = await get_challenge(db, body.challenge_id)
    cid = correlation_id or new_correlation_id()
    override_id = f"wovr-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    doc = {
        "override_id": override_id,
        "challenge_id": body.challenge_id,
        "policy_key": body.policy_key,
        "reason": body.reason,
        "override_effect": body.override_effect,
        "status": "proposed",
        "tenant_id": ch.get("tenant_id"),
        "correlation_id": cid,
        "lineage": LineageEnvelope.from_request(correlation_id=cid).to_dict(),
        "created_at": now,
        "updated_at": now,
    }
    await db.workflow_overrides.insert_one(doc)
    await write_workforce_audit(db, action="workflow_override_record", outcome="proposed", scope=scope, correlation_id=cid, context={"override_id": override_id}, event_type=GOVERNANCE_AUDIT_EVENT)
    return serialize_doc(doc)


async def apply_workflow_override(db, override_id: str, scope):
    doc = await db.workflow_overrides.find_one({"override_id": override_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Override not found")
    now = datetime.now(timezone.utc)
    await db.workflow_overrides.update_one({"override_id": override_id}, {"$set": {"status": "applied", "updated_at": now}})
    return serialize_doc(await db.workflow_overrides.find_one({"override_id": override_id}))
