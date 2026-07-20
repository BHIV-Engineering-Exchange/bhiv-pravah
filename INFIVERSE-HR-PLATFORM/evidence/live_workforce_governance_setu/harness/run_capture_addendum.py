"""Live WO/GE/SETU Sprint ADDENDUM capture — added after reading the real Review Feedback file.

Closes the gaps the actual reviewer emphasised beyond Implementation.md:
- Finding #3 "Workforce Runtime Needs Real Organizational Proof" -> explicit
  MULTI-ORG structure (two organizations under one platform) + org-scoped
  listing isolation + role inheritance + transfer (already in main capture).
- Finding #5 "Decision Ledger Needs Replay Demonstration" -> a consolidated
  Decision -> Challenge -> Review -> Override -> Final-State replay packet
  reconstructed by one scenario correlation_id (workforce trace-replay AND
  control-center audit-replay).

No runtime/code changes: uses only existing endpoints. Same in-process / in-memory
runtime as run_capture.py (local in-process; not deployed). Output: evidence/live_workforce_governance_setu/addendum/.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("API_KEY_SECRET", "live_workforce_governance_setu-harness-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "live_workforce_governance_setu-harness-jwt-secret")
os.environ.setdefault("CANDIDATE_JWT_SECRET_KEY", "live_workforce_governance_setu-harness-candidate-secret")
os.environ.setdefault("DATABASE_URL", "mongodb://in-memory.local/bhiv_hr")
os.environ.setdefault("MONGODB_URI", "mongodb://in-memory.local/bhiv_hr")
os.environ.setdefault("MONGODB_DB_NAME", "bhiv_hr")

REPO_ROOT = Path(__file__).resolve().parents[3]
GATEWAY_ROOT = REPO_ROOT / "backend" / "services" / "gateway"
sys.path.insert(0, str(GATEWAY_ROOT))

from fastapi import Depends, FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

import routes.workforce_governance_routes as wroutes  # noqa: E402
from app.control_center_governance import assert_control_center_access, build_audit_replay, list_audit_events  # noqa: E402
from jwt_auth import get_auth  # noqa: E402

_mock_db = AsyncMongoMockClient()["bhiv_hr"]


async def _get_db_override():
    return _mock_db


wroutes.get_mongo_db = _get_db_override

app = FastAPI(title="Live WO/GE/SETU Sprint Addendum Harness")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


app.include_router(wroutes.router)


@app.get("/v1/control-center/audit-events")
async def cc_audit_events(auth=Depends(get_auth), correlation_id: str = None, limit: int = 50):
    scope = assert_control_center_access(auth)
    return await list_audit_events(_mock_db, scope, correlation_id=correlation_id, limit=limit)


@app.get("/v1/control-center/audit-replay")
async def cc_audit_replay(auth=Depends(get_auth), correlation_id: str = None, limit: int = 20):
    scope = assert_control_center_access(auth)
    return await build_audit_replay(_mock_db, scope, correlation_id=correlation_id, limit=limit)


client = TestClient(app)
TOKEN = os.environ["API_KEY_SECRET"]
CAPTURES = []


def call(method, path, *, json_body=None, cid=None, note=""):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if cid:
        headers["X-Correlation-ID"] = cid
    ts = datetime.now(timezone.utc).isoformat()
    resp = client.request(method, path, json=json_body, headers=headers)
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text}
    rec = {"note": note, "method": method, "path": path, "request_body": json_body,
           "http_status": resp.status_code, "timestamp_utc": ts, "response_body": body}
    CAPTURES.append(rec)
    return resp.status_code, body, rec


def dump(rel, obj):
    out = REPO_ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def main():
    result = {"environment": "local in-process FastAPI runtime over in-memory async Mongo (mongomock_motor); not deployed",
              "captured_at": datetime.now(timezone.utc).isoformat(), "multi_org": {}, "replay_packet": {}}

    # ---------- Finding #3: MULTI-ORG STRUCTURE ----------
    orgs = {}
    for tag, name, code, role in [("X", "Civic Services Org", "ORG-X-T21", "civic_member"),
                                  ("Y", "Logistics Authority Org", "ORG-Y-T21", "logi_member")]:
        _, org, _ = call("POST", "/v1/workforce/organizations",
                         json_body={"name": name, "code": code, "default_roles": [role], "status": "active"},
                         note=f"create organization {tag}")
        _, dept, _ = call("POST", "/v1/workforce/departments",
                          json_body={"organization_id": org["id"], "name": f"{tag} Operations", "code": f"DEPT-{tag}-T21",
                                     "default_roles": ["specialist"], "status": "active"},
                          note=f"create department in org {tag}")
        _, emp, _ = call("POST", "/v1/workforce/employees",
                         json_body={"organization_id": org["id"], "department_id": dept["id"],
                                    "workforce_type": "employee", "role": "specialist",
                                    "display_name": f"Emp-{tag}", "lifecycle_state": "draft", "source_system": "sampada"},
                         note=f"create employee in org {tag}")
        orgs[tag] = {"org_id": org["id"], "dept_id": dept["id"], "employee_id": emp["id"],
                     "workforce_ref_id": emp["workforce_ref_id"], "inherited_roles": emp["inherited_roles"]}

    _, listX, _ = call("GET", f"/v1/workforce/employees?organization_id={orgs['X']['org_id']}", note="list employees scoped to org X")
    _, listY, _ = call("GET", f"/v1/workforce/employees?organization_id={orgs['Y']['org_id']}", note="list employees scoped to org Y")
    refsX = {e["workforce_ref_id"] for e in listX.get("items", [])}
    refsY = {e["workforce_ref_id"] for e in listY.get("items", [])}
    result["multi_org"] = {
        "orgs": orgs,
        "org_X_employee_count": len(listX.get("items", [])),
        "org_Y_employee_count": len(listY.get("items", [])),
        "org_lists_disjoint": refsX.isdisjoint(refsY),
        "org_X_refs": sorted(refsX), "org_Y_refs": sorted(refsY),
    }

    # ---------- Finding #5: CONSOLIDATED REPLAY PACKET ----------
    SCEN_CID = str(uuid.uuid4())
    result["replay_packet"]["correlation_id"] = SCEN_CID
    call("POST", "/v1/policies/definitions",
         json_body={"policy_key": "approval_policy", "name": "Approval Policy", "description": "addendum replay packet",
                    "version": "1.0.0", "rules": {"require_explicit_approval": True, "effect": "deny_until_approved"}, "scope_type": "tenant"},
         note="[packet] policy definition")
    _, ev, _ = call("POST", "/v1/policies/evaluate", cid=SCEN_CID,
                    json_body={"policy_key": "approval_policy", "context": {"approved": False}}, note="[packet] evaluate (deny)")
    _, ch, _ = call("POST", "/v1/governance/challenges", cid=SCEN_CID,
                    json_body={"policy_key": "approval_policy", "evaluation_id": ev["evaluation_id"],
                               "subject_type": "policy_evaluation", "subject_id": ev["evaluation_id"], "reason": "Challenge denial"},
                    note="[packet] challenge")
    _, rev, _ = call("POST", "/v1/governance/reviews", cid=SCEN_CID,
                     json_body={"challenge_id": ch["challenge_id"], "reviewer_role": "admin", "notes": "assigned"}, note="[packet] review assign")
    _, revc, _ = call("POST", f"/v1/governance/reviews/{rev['review_id']}/complete",
                      json_body={"outcome": "upheld", "notes": "upheld"}, note="[packet] review complete")
    _, ovr, _ = call("POST", "/v1/governance/overrides", cid=SCEN_CID,
                     json_body={"challenge_id": ch["challenge_id"], "policy_key": "approval_policy", "reason": "override", "override_effect": "allow"},
                     note="[packet] override propose")
    _, ovra, _ = call("POST", f"/v1/governance/overrides/{ovr['override_id']}/apply", note="[packet] override apply")
    _, dec, _ = call("POST", "/v1/decisions", cid=SCEN_CID,
                     json_body={"owner": "Rishabh Yadav", "scope": "tenant", "rationale": "final decision for packet",
                                "inputs": {"evaluation_id": ev["evaluation_id"], "override_id": ovr["override_id"]},
                                "challenge_id": ch["challenge_id"], "review_id": rev["review_id"], "trace_references": [SCEN_CID]},
                     note="[packet] decision record")
    _, wf_replay, _ = call("GET", f"/v1/workforce/trace-replay?correlation_id={SCEN_CID}", note="[packet] consolidated replay via workforce trace-replay")
    _, cc_replay, _ = call("GET", f"/v1/control-center/audit-replay?correlation_id={SCEN_CID}", note="[packet] consolidated replay via control-center audit-replay")
    result["replay_packet"].update({
        "ids": {"evaluation_id": ev["evaluation_id"], "challenge_id": ch["challenge_id"], "review_id": rev["review_id"],
                "review_outcome": revc.get("outcome"), "override_id": ovr["override_id"], "override_status": ovra.get("status"),
                "decision_id": dec["decision_id"]},
        "trace_replay_actions": [e["action"] for e in wf_replay.get("events", [])],
        "trace_replay_count": wf_replay.get("event_count"),
        "control_center_replay_ops": [e["op"] for e in cc_replay.get("events", [])],
        "control_center_replay_count": cc_replay.get("count"),
    })

    dump("evidence/live_workforce_governance_setu/addendum/multiorg_and_replay_packet.json",
         {"summary": result, "calls": CAPTURES})

    print("MULTI-ORG: X=%s Y=%s disjoint=%s" % (result["multi_org"]["org_X_employee_count"],
                                                 result["multi_org"]["org_Y_employee_count"],
                                                 result["multi_org"]["org_lists_disjoint"]))
    print("ORG X:", orgs["X"]["org_id"], "ORG Y:", orgs["Y"]["org_id"])
    print("PACKET CID:", SCEN_CID)
    print("PACKET trace-replay actions:", result["replay_packet"]["trace_replay_actions"])
    print("PACKET cc-replay ops:", result["replay_packet"]["control_center_replay_ops"])
    print("PACKET ids:", json.dumps(result["replay_packet"]["ids"]))
    print("TOTAL CALLS:", len(CAPTURES))
    print("OK")


if __name__ == "__main__":
    main()
