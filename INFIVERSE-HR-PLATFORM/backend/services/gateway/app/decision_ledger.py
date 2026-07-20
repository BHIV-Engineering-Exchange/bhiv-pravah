"""Decision ledger storage and replay reconstruction."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.lineage_envelope import LineageEnvelope
from app.workforce_common import GOVERNANCE_AUDIT_EVENT, new_correlation_id, serialize_doc, tenant_id_for_scope, write_workforce_audit


class DecisionCreate(BaseModel):
    owner: str
    scope: str
    rationale: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    status: str = "active"
    supersedes: Optional[str] = None
    trace_references: List[str] = Field(default_factory=list)
    challenge_id: Optional[str] = None
    review_id: Optional[str] = None


async def create_decision(db, body: DecisionCreate, scope, correlation_id=None):
    cid = correlation_id or new_correlation_id()
    decision_id = f"dec-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    envelope = LineageEnvelope.from_request(correlation_id=cid)
    trace_refs = list(body.trace_references)
    if cid not in trace_refs:
        trace_refs.append(cid)
    if body.supersedes:
        if not await db.decisions.find_one({"decision_id": body.supersedes}):
            raise HTTPException(status_code=404, detail="Prior decision not found")
        await db.decisions.update_one({"decision_id": body.supersedes}, {"$set": {"status": "superseded", "updated_at": now}})
    doc = {
        "decision_id": decision_id,
        "owner": body.owner,
        "scope": body.scope,
        "rationale": body.rationale,
        "inputs": body.inputs,
        "timestamp": now,
        "dependencies": body.dependencies,
        "status": body.status,
        "supersedes": body.supersedes,
        "trace_references": trace_refs,
        "challenge_id": body.challenge_id,
        "review_id": body.review_id,
        "tenant_id": tenant_id_for_scope(scope),
        "correlation_id": cid,
        "trace_id": envelope.trace_id,
        "lineage": envelope.to_dict(),
        "created_at": now,
        "updated_at": now,
    }
    await db.decisions.insert_one(doc)
    await write_workforce_audit(db, action="decision_record", outcome="recorded", scope=scope, correlation_id=cid, context={"decision_id": decision_id}, event_type=GOVERNANCE_AUDIT_EVENT)
    return serialize_doc(doc)


async def get_decision(db, decision_id: str):
    doc = await db.decisions.find_one({"decision_id": decision_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Decision not found")
    return serialize_doc(doc)


async def list_decisions(db, scope, limit=50):
    q = {} if scope.get("scope") == "platform" else {"tenant_id": tenant_id_for_scope(scope)}
    docs = await db.decisions.find(q).sort("timestamp", -1).limit(limit).to_list(limit)
    return [serialize_doc(d) for d in docs]


async def replay_decisions(db, decision_id=None, correlation_id=None, limit=50):
    if decision_id:
        root = await get_decision(db, decision_id)
        chain = [root]
        current_id = root.get("supersedes")
        visited = {root["decision_id"]}
        while current_id and len(chain) < limit:
            if current_id in visited:
                break
            prior = await db.decisions.find_one({"decision_id": current_id})
            if not prior:
                break
            serialized = serialize_doc(prior)
            chain.append(serialized)
            visited.add(current_id)
            current_id = serialized.get("supersedes")
        chain.reverse()
        return {"replay_type": "supersedes_chain", "root_decision_id": decision_id, "chain": chain}
    q: Dict[str, Any] = {}
    if correlation_id:
        q["correlation_id"] = correlation_id
    docs = await db.decisions.find(q).sort("timestamp", 1).limit(limit).to_list(limit)
    return {"replay_type": "correlation_timeline", "correlation_id": correlation_id, "decisions": [serialize_doc(d) for d in docs]}


async def record_decision_from_review(db, review_id: str, owner: str, rationale: str, scope):
    review = await db.reviews.find_one({"review_id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return await create_decision(
        db,
        DecisionCreate(
            owner=owner,
            scope=tenant_id_for_scope(scope),
            rationale=rationale,
            inputs={"review_id": review_id, "outcome": review.get("outcome")},
            challenge_id=review.get("challenge_id"),
            review_id=review_id,
            trace_references=[review.get("correlation_id", "")],
        ),
        scope,
        correlation_id=review.get("correlation_id"),
    )
