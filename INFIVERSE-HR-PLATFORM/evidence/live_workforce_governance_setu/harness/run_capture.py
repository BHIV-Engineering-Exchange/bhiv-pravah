"""Live WO/GE/SETU Sprint continuous evidence-capture harness.

Drives the EXISTING workforce / governance / SETU runtime through realistic,
linked scenarios using the real FastAPI route layer (no behavior changes).

Execution environment:
- In-process FastAPI app mounting the real `workforce_governance_routes` router
  plus the two real Control Center audit read endpoints (replicated verbatim
  from app/main.py wiring) so Phase 7 reads use the same runtime functions.
- Persistence: in-memory async Mongo (mongomock_motor) — an ephemeral, real
  Motor-compatible store. This is a LOCAL in-process runtime capture, NOT the
  deployed Render gateway and NOT a persistent Mongo. Every request/response/
  status/timestamp below is genuinely produced by the runtime in this session.

Auth:
- admin/platform scope via API key (API_KEY_SECRET).
- client/tenant scope via HS256 JWT (JWT_SECRET_KEY) for boundary checks.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- env must be set before importing app modules ---
os.environ.setdefault("API_KEY_SECRET", "live_workforce_governance_setu-harness-api-key")
os.environ.setdefault("JWT_SECRET_KEY", "live_workforce_governance_setu-harness-jwt-secret")
os.environ.setdefault("CANDIDATE_JWT_SECRET_KEY", "live_workforce_governance_setu-harness-candidate-secret")
os.environ.setdefault("DATABASE_URL", "mongodb://in-memory.local/bhiv_hr")
os.environ.setdefault("MONGODB_URI", "mongodb://in-memory.local/bhiv_hr")
os.environ.setdefault("MONGODB_DB_NAME", "bhiv_hr")

REPO_ROOT = Path(__file__).resolve().parents[3]
GATEWAY_ROOT = REPO_ROOT / "backend" / "services" / "gateway"
sys.path.insert(0, str(GATEWAY_ROOT))

import jwt  # noqa: E402
from fastapi import Depends, FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

import uuid  # noqa: E402

import routes.workforce_governance_routes as wroutes  # noqa: E402
from app.control_center_governance import (  # noqa: E402
    assert_control_center_access,
    build_audit_replay,
    list_audit_events,
)
from jwt_auth import get_auth  # noqa: E402

# --- shared in-memory db, patched into the routes module ---
_mock_client = AsyncMongoMockClient()
_mock_db = _mock_client["bhiv_hr"]


async def _get_db_override():
    return _mock_db


wroutes.get_mongo_db = _get_db_override  # patch the name used inside route handlers

app = FastAPI(title="Live WO/GE/SETU Sprint Capture Harness")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


app.include_router(wroutes.router)


# Control Center read endpoints — wiring copied from app/main.py (real functions)
@app.get("/v1/control-center/audit-events")
async def cc_audit_events(auth=Depends(get_auth), correlation_id: str = None, limit: int = 50):
    scope = assert_control_center_access(auth)
    return await list_audit_events(_mock_db, scope, correlation_id=correlation_id, limit=limit)


@app.get("/v1/control-center/audit-replay")
async def cc_audit_replay(auth=Depends(get_auth), correlation_id: str = None, limit: int = 20):
    scope = assert_control_center_access(auth)
    return await build_audit_replay(_mock_db, scope, correlation_id=correlation_id, limit=limit)


client = TestClient(app)

ADMIN_TOKEN = os.environ["API_KEY_SECRET"]
CLIENT_ID = "TENANT-CLIENT-01"
CLIENT_TOKEN = jwt.encode(
    {"sub": CLIENT_ID, "role": "client", "email": "ops@tenant-client-01.local"},
    os.environ["JWT_SECRET_KEY"],
    algorithm="HS256",
)

CAPTURES = []


def call(method, path, *, token=ADMIN_TOKEN, json_body=None, cid=None, note=""):
    headers = {"Authorization": f"Bearer {token}"}
    if cid:
        headers["X-Correlation-ID"] = cid
    ts = datetime.now(timezone.utc).isoformat()
    resp = client.request(method, path, json=json_body, headers=headers)
    try:
        body = resp.json()
    except Exception:
        body = {"_raw": resp.text}
    rec = {
        "note": note,
        "method": method,
        "path": path,
        "request_correlation_id_header": cid,
        "request_body": json_body,
        "auth": "api_key:admin" if token == ADMIN_TOKEN else "jwt:client",
        "http_status": resp.status_code,
        "response_correlation_id_header": resp.headers.get("X-Correlation-ID"),
        "timestamp_utc": ts,
        "response_body": body,
    }
    CAPTURES.append(rec)
    return resp.status_code, body, rec


def dump(rel_path, obj):
    out = REPO_ROOT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    return str(out)


def main():
    index = {
        "task": "Live WO/GE/SETU Sprint",
        "environment": "local in-process FastAPI runtime over in-memory async Mongo (mongomock_motor)",
        "deployed": False,
        "gateway_base_url": "in-process://gateway (real workforce_governance_routes router)",
        "auth_admin": "api_key (platform/admin scope)",
        "auth_client": "HS256 JWT (client/tenant scope = %s)" % CLIENT_ID,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "ids": {},
        "phases": {},
    }

    # ===================== PHASE 1 — Live Workforce Operations =====================
    p1 = {"calls": []}
    LIFE_CID = str(uuid.uuid4())  # one correlation id threading the whole employee lifecycle
    index["ids"]["lifecycle_correlation_id"] = LIFE_CID

    _, org, r = call("POST", "/v1/workforce/organizations", cid=LIFE_CID,
                     json_body={"name": "Sampada National Operations", "code": "SNO-T21",
                                "default_roles": ["org_member"], "status": "active"}, note="create organization")
    p1["calls"].append(r)
    org_id = org["id"]

    _, div, r = call("POST", "/v1/workforce/divisions", cid=LIFE_CID,
                     json_body={"organization_id": org_id, "name": "Field Operations Division",
                                "code": "FOD-T21", "status": "active"}, note="create division")
    p1["calls"].append(r)
    div_id = div["id"]

    _, unit, r = call("POST", "/v1/workforce/units", cid=LIFE_CID,
                      json_body={"division_id": div_id, "name": "Northern Unit", "code": "NU-T21",
                                 "status": "active"}, note="create unit")
    p1["calls"].append(r)
    unit_id = unit["id"]

    _, deptA, r = call("POST", "/v1/workforce/departments", cid=LIFE_CID,
                       json_body={"organization_id": org_id, "unit_id": unit_id, "name": "Onboarding Desk",
                                  "code": "DEPT-A-T21", "default_roles": ["analyst"],
                                  "teams": [{"team_id": "tm-a1", "name": "Intake Team", "lead_role": "lead"}],
                                  "status": "active"}, note="create department A (with team)")
    p1["calls"].append(r)
    deptA_id = deptA["id"]

    _, deptB, r = call("POST", "/v1/workforce/departments", cid=LIFE_CID,
                       json_body={"organization_id": org_id, "unit_id": unit_id, "name": "Regional Operations",
                                  "code": "DEPT-B-T21", "default_roles": ["operations_specialist"],
                                  "status": "active"}, note="create department B")
    p1["calls"].append(r)
    deptB_id = deptB["id"]

    _, deptC, r = call("POST", "/v1/workforce/departments", cid=LIFE_CID,
                       json_body={"organization_id": org_id, "unit_id": unit_id, "name": "Strategic Programs",
                                  "code": "DEPT-C-T21", "default_roles": ["program_lead"],
                                  "status": "active"}, note="create department C")
    p1["calls"].append(r)
    deptC_id = deptC["id"]

    _, emp, r = call("POST", "/v1/workforce/employees", cid=LIFE_CID,
                     json_body={"organization_id": org_id, "department_id": deptA_id,
                                "workforce_type": "employee", "role": "analyst",
                                "display_name": "R. Mehta", "email": "r.mehta@tenant-client-01.local",
                                "lifecycle_state": "draft", "source_system": "sampada"}, note="create employee (draft)")
    p1["calls"].append(r)
    emp_id = emp["id"]
    wf_ref = emp["workforce_ref_id"]
    index["ids"].update({"org_id": org_id, "division_id": div_id, "unit_id": unit_id,
                         "department_a_id": deptA_id, "department_b_id": deptB_id, "department_c_id": deptC_id,
                         "employee_id": emp_id, "workforce_ref_id": wf_ref})

    _, _, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/onboard", cid=LIFE_CID,
                   json_body={"reason": "Start onboarding"}, note="lifecycle: onboard (draft->onboarding)")
    p1["calls"].append(r)
    _, _, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/onboard-complete", cid=LIFE_CID,
                   json_body={"reason": "Onboarding complete; assigned active"}, note="lifecycle: onboard-complete (onboarding->active) = ASSIGNED")
    p1["calls"].append(r)
    _, _, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/department-transfer", cid=LIFE_CID,
                   json_body={"new_department_id": deptB_id, "reason": "Transfer to Regional Operations"},
                   note="lifecycle: department-transfer -> dept B = TRANSFERRED")
    p1["calls"].append(r)
    _, promo, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/role-move", cid=LIFE_CID,
                       json_body={"new_role": "operations_manager", "transition_type": "promotion",
                                  "reason": "Promotion to operations_manager"},
                       note="lifecycle: role-move transition_type=promotion = PROMOTED (Gap Fix #1)")
    p1["calls"].append(r)
    _, _, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/department-transfer", cid=LIFE_CID,
                   json_body={"new_department_id": deptC_id, "reason": "Move to Strategic Programs"},
                   note="lifecycle: department-transfer -> dept C = MOVED (Gap Resolution #3)")
    p1["calls"].append(r)
    _, _, r = call("POST", f"/v1/workforce/employees/{emp_id}/lifecycle/offboard-prepare", cid=LIFE_CID,
                   json_body={"reason": "Begin offboarding preparation"},
                   note="lifecycle: offboard-prepare = OFFBOARDING INITIATED")
    p1["calls"].append(r)

    _, replay, r = call("GET", f"/v1/workforce/trace-replay?correlation_id={LIFE_CID}", note="REPLAY RECONSTRUCTION (workforce trace-replay by correlation_id)")
    p1["calls"].append(r)
    p1["replay"] = replay
    index["phases"]["phase1"] = {
        "replay_event_count": replay.get("event_count"),
        "replay_actions": [e["action"] for e in replay.get("events", [])],
    }
    dump("evidence/live_workforce_governance_setu/workforce_operations/phase1_capture.json", p1)

    # ===================== PHASE 2 — Org Hierarchy Validation =====================
    p2 = {"calls": []}
    # role-inheritance-only employee (role set only through department default_roles propagation)
    _, emp2, r = call("POST", "/v1/workforce/employees",
                      json_body={"organization_id": org_id, "department_id": deptA_id,
                                 "workforce_type": "consultant", "role": "analyst",
                                 "display_name": "S. Iyer", "email": "s.iyer@tenant-client-01.local",
                                 "lifecycle_state": "draft", "source_system": "sampada"},
                      note="create employee in dept A to demonstrate inherited_roles (org+dept defaults)")
    p2["calls"].append(r)
    _, emp3, r = call("POST", "/v1/workforce/employees",
                      json_body={"organization_id": org_id, "department_id": deptB_id,
                                 "workforce_type": "employee", "role": "operations_specialist",
                                 "display_name": "K. Rao", "email": "k.rao@tenant-client-01.local",
                                 "lifecycle_state": "draft", "source_system": "sampada"},
                      note="create employee in dept B (different role)")
    p2["calls"].append(r)
    index["ids"]["employee2_id"] = emp2["id"]
    index["ids"]["employee2_inherited_roles"] = emp2.get("inherited_roles")
    index["ids"]["employee3_id"] = emp3["id"]

    _, hier, r = call("GET", f"/v1/workforce/organizations/{org_id}/hierarchy", note="org hierarchy traversal (full nested tree)")
    p2["calls"].append(r)
    p2["hierarchy"] = hier

    # visibility boundary: admin/platform sees all; client/tenant sees only its tenant
    _, admin_list, r = call("GET", "/v1/workforce/employees?organization_id=" + org_id, note="employee list under ADMIN/platform scope")
    p2["calls"].append(r)
    _, client_list, r = call("GET", "/v1/workforce/employees", token=CLIENT_TOKEN, note="employee list under CLIENT/tenant scope (boundary check)")
    p2["calls"].append(r)
    index["phases"]["phase2"] = {
        "admin_visible_employees": len(admin_list.get("items", [])),
        "client_visible_employees": len(client_list.get("items", [])),
        "admin_scope": admin_list.get("policy_scope", {}).get("scope"),
        "client_scope": client_list.get("policy_scope", {}).get("scope"),
    }

    # negative path: foreign / unknown organization id
    _, foreign, r = call("GET", "/v1/workforce/organizations/000000000000000000000000/hierarchy", note="negative-path: unknown organization_id (expect 404)")
    p2["calls"].append(r)
    index["phases"]["phase2"]["foreign_org_status"] = r["http_status"]
    dump("evidence/live_workforce_governance_setu/workforce_operations/phase2_hierarchy.json", p2)

    # ===================== PHASE 3 — Governance Exercise & Replay =====================
    p3 = {"scenarios": []}
    scenarios = [
        {"key": "leave_policy", "name": "Leave Policy", "rules": {"min_tenure_days": 90, "effect": "observe"},
         "eval_ctx": {"tenure_days": 10}, "domain": "Leave"},
        {"key": "visibility_policy", "name": "Visibility Policy", "rules": {"require_scope_match": True, "effect": "allow"},
         "eval_ctx": {"scope_match": False}, "domain": "Visibility"},
        {"key": "approval_policy", "name": "Approval Policy", "rules": {"require_explicit_approval": True, "effect": "deny_until_approved"},
         "eval_ctx": {"approved": False}, "domain": "Approval"},
    ]
    gov_index = []
    for sc in scenarios:
        s = {"domain": sc["domain"], "calls": []}
        SCEN_CID = str(uuid.uuid4())
        s["correlation_id"] = SCEN_CID
        _, pol, r = call("POST", "/v1/policies/definitions",
                         json_body={"policy_key": sc["key"], "name": sc["name"], "description": f"{sc['domain']} governance scenario",
                                    "version": "1.0.0", "rules": sc["rules"], "scope_type": "tenant"},
                         note=f"[{sc['domain']}] policy definition create")
        s["calls"].append(r); s["policy_id"] = pol["id"]
        _, ev, r = call("POST", "/v1/policies/evaluate", cid=SCEN_CID,
                        json_body={"policy_key": sc["key"], "context": sc["eval_ctx"]},
                        note=f"[{sc['domain']}] policy evaluate (expect deny -> motivates challenge)")
        s["calls"].append(r); s["evaluation_id"] = ev["evaluation_id"]; s["evaluation_result"] = ev["result"]
        _, ch, r = call("POST", "/v1/governance/challenges", cid=SCEN_CID,
                        json_body={"policy_key": sc["key"], "evaluation_id": ev["evaluation_id"],
                                   "subject_type": "policy_evaluation", "subject_id": ev["evaluation_id"],
                                   "reason": f"Challenge {sc['domain']} denial for review"},
                        note=f"[{sc['domain']}] challenge raise")
        s["calls"].append(r); s["challenge_id"] = ch["challenge_id"]
        _, rev, r = call("POST", "/v1/governance/reviews", cid=SCEN_CID,
                         json_body={"challenge_id": ch["challenge_id"], "reviewer_role": "admin",
                                    "notes": "Assigned for governance review"},
                         note=f"[{sc['domain']}] review assign")
        s["calls"].append(r); s["review_id"] = rev["review_id"]
        _, revc, r = call("POST", f"/v1/governance/reviews/{rev['review_id']}/complete",
                          json_body={"outcome": "upheld", "notes": "Review upheld; override warranted"},
                          note=f"[{sc['domain']}] review complete (upheld)")
        s["calls"].append(r); s["review_outcome"] = revc.get("outcome")
        _, ovr, r = call("POST", "/v1/governance/overrides", cid=SCEN_CID,
                         json_body={"challenge_id": ch["challenge_id"], "policy_key": sc["key"],
                                    "reason": f"Override {sc['domain']} outcome per review", "override_effect": "allow"},
                         note=f"[{sc['domain']}] workflow override propose")
        s["calls"].append(r); s["override_id"] = ovr["override_id"]
        _, ovra, r = call("POST", f"/v1/governance/overrides/{ovr['override_id']}/apply",
                          note=f"[{sc['domain']}] workflow override apply")
        s["calls"].append(r); s["override_status"] = ovra.get("status")
        _, dec, r = call("POST", "/v1/decisions", cid=SCEN_CID,
                         json_body={"owner": "Rishabh Yadav", "scope": "tenant",
                                    "rationale": f"Recorded decision for {sc['domain']} challenge {ch['challenge_id']}",
                                    "inputs": {"evaluation_id": ev["evaluation_id"], "override_id": ovr["override_id"]},
                                    "challenge_id": ch["challenge_id"], "review_id": rev["review_id"],
                                    "trace_references": [SCEN_CID]},
                         note=f"[{sc['domain']}] decision record")
        s["calls"].append(r); s["decision_id"] = dec["decision_id"]

        # Scenario A only: record a superseding decision to prove a real replay chain
        if sc["domain"] == "Leave":
            _, dec2, r = call("POST", "/v1/decisions", cid=SCEN_CID,
                              json_body={"owner": "Rishabh Yadav", "scope": "tenant",
                                         "rationale": "Corrected leave decision superseding prior",
                                         "inputs": {"correction": True}, "supersedes": dec["decision_id"],
                                         "trace_references": [SCEN_CID]},
                              note="[Leave] superseding decision (supersedes prior) for replay chain")
            s["calls"].append(r); s["superseding_decision_id"] = dec2["decision_id"]
            replay_target = dec2["decision_id"]
        else:
            replay_target = dec["decision_id"]

        _, drep, r = call("GET", f"/v1/decisions/replay?decision_id={replay_target}",
                          note=f"[{sc['domain']}] decision replay (supersedes chain)")
        s["calls"].append(r); s["replay"] = drep
        s["replay_chain_len"] = len(drep.get("chain", []))
        p3["scenarios"].append(s)
        gov_index.append({k: s.get(k) for k in ("domain", "correlation_id", "policy_id", "evaluation_id",
                                                "challenge_id", "review_id", "override_id", "decision_id",
                                                "superseding_decision_id", "replay_chain_len")})
    index["phases"]["phase3"] = gov_index
    dump("evidence/live_workforce_governance_setu/governance_replay/phase3_scenarios.json", p3)

    # ===================== PHASE 4 — Policy Replay Validation (policy-state angle) =====================
    p4 = {"calls": []}
    _, poldefs, r = call("GET", "/v1/policies/definitions?limit=50", note="list policy definitions (post-scenario state)")
    p4["calls"].append(r)
    p4["definitions"] = poldefs
    # re-evaluate each policy with a compliant context to show post-override 'allow' state vs prior deny
    reeval = []
    for sc, ctx in [("leave_policy", {"tenure_days": 200}), ("visibility_policy", {"scope_match": True}), ("approval_policy", {"approved": True})]:
        _, ev, r = call("POST", "/v1/policies/evaluate", json_body={"policy_key": sc, "context": ctx},
                        note=f"re-evaluate {sc} with compliant context (state comparison vs Phase 3 deny)")
        p4["calls"].append(r)
        reeval.append({"policy_key": sc, "result": ev["result"], "evaluation_id": ev["evaluation_id"]})
    p4["reevaluations"] = reeval
    index["phases"]["phase4"] = {"definition_count": len(poldefs.get("items", [])), "reevaluations": reeval}
    dump("evidence/live_workforce_governance_setu/governance_replay/phase4_policy_state.json", p4)

    # ===================== PHASE 5 — Live SETU Participation =====================
    p5 = {"signals": []}
    signal_specs = [
        {"type": "niyantran_telemetry", "payload": {"event": "task_completed", "task_id": "exec-7781", "workforce_ref": wf_ref},
         "linked": True, "trust": "observed"},
        {"type": "artha_payroll_visibility", "payload": {"period": "2026-06", "visibility": "summary_only", "workforce_ref": wf_ref}, "trust": "observed"},
        {"type": "crm_participation", "payload": {"interaction": "client_touchpoint", "account": "TENANT-CLIENT-01"}, "trust": "observed"},
        {"type": "setu_aggregation", "payload": {"aggregate": "cross_system_rollup", "sources": ["niyantran", "artha", "crm"]}, "trust": "derived"},
    ]
    for spec in signal_specs:
        body = {"payload": spec["payload"], "workforce_ref_id": wf_ref,
                "source_declaration": f"{spec['type']} participation", "trust_classification": spec["trust"],
                "visibility_scope": "tenant"}
        # Link the niyantran signal to the lifecycle correlation/trace to prove cross-system continuity
        if spec.get("linked"):
            body["correlation_id"] = LIFE_CID
            body["trace_id"] = LIFE_CID
        _, sig, r = call("POST", f"/v1/setu/signals/{spec['type']}", json_body=body,
                         note=f"SETU ingest {spec['type']}" + (" (linked to lifecycle trace)" if spec.get("linked") else ""))
        entry = {"signal_type": spec["type"], "ingest": r, "signal_id": sig.get("signal_id"),
                 "trace_id": sig.get("lineage", {}).get("trace_id"), "owning_system": sig.get("lineage", {}).get("owning_system")}
        # list back by signal_type + correlation_id
        cidq = sig.get("lineage", {}).get("correlation_id")
        _, lst, r2 = call("GET", f"/v1/setu/signals?signal_type={spec['type']}&correlation_id={cidq}",
                          note=f"SETU list {spec['type']} by correlation_id")
        entry["list"] = r2
        # trace continuity
        _, tr, r3 = call("GET", f"/v1/setu/trace/{entry['trace_id']}", note=f"SETU trace continuity for {spec['type']}")
        entry["trace"] = r3
        entry["trace_signal_count"] = tr.get("signal_count")
        entry["trace_audit_count"] = tr.get("audit_count")
        p5["signals"].append(entry)
    index["phases"]["phase5"] = [
        {"signal_type": e["signal_type"], "signal_id": e["signal_id"], "trace_id": e["trace_id"],
         "owning_system": e["owning_system"], "trace_signal_count": e["trace_signal_count"],
         "trace_audit_count": e["trace_audit_count"]} for e in p5["signals"]
    ]
    dump("evidence/live_workforce_governance_setu/setu_participation/phase5_signals.json", p5)

    # ===================== PHASE 6 — Ownership Metadata & Lineage =====================
    # cross-system trace: the niyantran signal shares LIFE_CID trace with workforce lifecycle audits
    _, life_trace, _ = call("GET", f"/v1/setu/trace/{LIFE_CID}", note="Phase6 cross-system trace continuity on lifecycle correlation id")
    p6 = {
        "lifecycle_correlation_id": LIFE_CID,
        "cross_system_trace": life_trace,
        "samples": {
            "workforce_employee_lineage": emp.get("lineage"),
            "governance_decision_lineage": p3["scenarios"][0]["calls"][-2]["response_body"].get("lineage")
            if p3["scenarios"][0]["calls"] else None,
            "setu_signal_lineage": p5["signals"][0]["ingest"]["response_body"].get("lineage"),
        },
    }
    index["phases"]["phase6"] = {
        "cross_system_trace_signal_count": life_trace.get("signal_count"),
        "cross_system_trace_audit_count": life_trace.get("audit_count"),
        "required_fields_present": sorted(list((emp.get("lineage") or {}).keys())),
    }
    dump("evidence/live_workforce_governance_setu/lineage/phase6_lineage.json", p6)

    # ===================== PHASE 7 — Control Center Operational Evidence =====================
    p7 = {"calls": []}
    _, ev_all, r = call("GET", "/v1/control-center/audit-events?limit=50", note="Control Center: scoped audit-events (admin/platform)")
    p7["calls"].append(r)
    _, ev_cid, r = call("GET", f"/v1/control-center/audit-events?correlation_id={LIFE_CID}", note="Control Center: audit-events filtered by lifecycle correlation_id")
    p7["calls"].append(r)
    _, rep, r = call("GET", f"/v1/control-center/audit-replay?correlation_id={LIFE_CID}", note="Control Center: audit-replay for lifecycle correlation_id")
    p7["calls"].append(r)
    p7["replay"] = rep
    index["phases"]["phase7"] = {
        "audit_events_total": ev_all.get("count"),
        "audit_events_for_lifecycle_cid": ev_cid.get("count"),
        "replay_event_count": rep.get("count"),
    }
    dump("evidence/live_workforce_governance_setu/control_center/phase7_control_center.json", p7)

    # ===================== master index + full capture =====================
    dump("evidence/live_workforce_governance_setu/capture_index.json", index)
    dump("evidence/live_workforce_governance_setu/full_capture.json", {"captures": CAPTURES})

    # status counts
    statuses = {}
    for c in CAPTURES:
        statuses[c["http_status"]] = statuses.get(c["http_status"], 0) + 1
    print("TOTAL CALLS:", len(CAPTURES))
    print("STATUS COUNTS:", statuses)
    print("LIFECYCLE_CID:", LIFE_CID)
    print("PHASE1 REPLAY ACTIONS:", index["phases"]["phase1"]["replay_actions"])
    print("PHASE6 cross-system trace: signals=%s audits=%s" % (
        index["phases"]["phase6"]["cross_system_trace_signal_count"],
        index["phases"]["phase6"]["cross_system_trace_audit_count"]))
    print("OK")


if __name__ == "__main__":
    main()
