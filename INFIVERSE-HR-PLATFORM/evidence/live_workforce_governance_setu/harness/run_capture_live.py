#!/usr/bin/env python3
"""Live deployment capture harness for Workforce/Governance/SETU evidence.

Uses deployed gateway URL and auth from backend/.env or current environment.
Writes additive evidence under evidence/live_workforce_governance_setu/live/.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = REPO_ROOT / "backend" / ".env"
OUT_ROOT = REPO_ROOT / "evidence" / "live_workforce_governance_setu" / "live"


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def main() -> int:
    load_env_file(ENV_PATH)

    gateway = (
        os.getenv("GATEWAY_URL")
        or os.getenv("GATEWAY_SERVICE_URL")
        or "https://bhiv-hr-gateway-l0xp.onrender.com"
    ).rstrip("/")
    api_key = os.getenv("API_KEY_SECRET") or os.getenv("API_KEY") or os.getenv("GATEWAY_SECRET_KEY") or ""
    timeout_s = float(os.getenv("E2E_HTTP_TIMEOUT", "45"))
    if not api_key:
        print("BLOCKER: missing API key secret in env.")
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_ROOT / run_id
    captures: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "run_id": run_id,
        "captured_at": now_utc(),
        "gateway_base_url": gateway,
        "environment": "deployed_live_gateway",
        "auth_method": "bearer_api_key",
        "status_counts": {},
        "phases": {},
        "ids": {},
        "blockers": [],
    }

    base_headers = {"Authorization": f"Bearer {api_key}"}
    lifecycle_cid = str(uuid.uuid4())
    summary["ids"]["lifecycle_correlation_id"] = lifecycle_cid

    def call(method: str, path: str, *, json_body: dict[str, Any] | None = None, cid: str | None = None, note: str = "") -> tuple[int, Any, dict[str, Any]]:
        headers = dict(base_headers)
        if cid:
            headers["X-Correlation-ID"] = cid
        ts = now_utc()
        url = f"{gateway}{path}"
        response = client.request(method, url, json=json_body, headers=headers)
        try:
            body = response.json()
        except Exception:
            body = {"_raw": response.text}
        rec = {
            "note": note,
            "method": method,
            "path": path,
            "timestamp_utc": ts,
            "request_correlation_id_header": cid,
            "http_status": response.status_code,
            "response_correlation_id_header": response.headers.get("x-correlation-id"),
            "request_body": json_body,
            "response_body": body,
        }
        captures.append(rec)
        return response.status_code, body, rec

    with httpx.Client(timeout=timeout_s) as client:
        p0: list[dict[str, Any]] = []
        for service in ["/health", "/metrics/dashboard", "/v1/workforce/organizations?limit=1"]:
            s, b, r = call("GET", service, note=f"health_or_reachability {service}")
            p0.append(r)
            if service == "/health" and s != 200:
                summary["blockers"].append(f"Gateway health check failed: HTTP {s}")
        summary["phases"]["phase0_health"] = p0

        p1: list[dict[str, Any]] = []
        org_id = div_id = unit_id = dept_a = dept_b = dept_c = emp_id = wf_ref = None
        s, b, r = call(
            "POST",
            "/v1/workforce/organizations",
            cid=lifecycle_cid,
            json_body={"name": f"Live Capture Org {run_id}", "code": f"LIVE-{run_id[-6:]}", "default_roles": ["org_member"], "status": "active"},
            note="phase1 create organization",
        )
        p1.append(r)
        if s in (200, 201):
            org_id = b.get("id")
        if not org_id:
            summary["blockers"].append(f"Organization create failed: HTTP {s}")
            summary["phases"]["phase1_workforce"] = p1
            dump_json(run_dir / "capture_index_live.json", summary)
            dump_json(run_dir / "full_capture_live.json", {"captures": captures})
            print(f"BLOCKED: phase1 start failed (HTTP {s})")
            return 1

        summary["ids"]["org_id"] = org_id
        for payload, path, key, note in [
            ({"organization_id": org_id, "name": "Live Division", "code": f"LD-{run_id[-6:]}", "status": "active"}, "/v1/workforce/divisions", "division_id", "phase1 create division"),
            (None, None, None, None),
        ]:
            if path:
                s, b, r = call("POST", path, cid=lifecycle_cid, json_body=payload, note=note)
                p1.append(r)
                if s in (200, 201):
                    summary["ids"][key] = b.get("id")
        div_id = summary["ids"].get("division_id")

        s, b, r = call(
            "POST",
            "/v1/workforce/units",
            cid=lifecycle_cid,
            json_body={"division_id": div_id, "name": "Live Unit", "code": f"LU-{run_id[-6:]}", "status": "active"},
            note="phase1 create unit",
        )
        p1.append(r)
        unit_id = b.get("id") if s in (200, 201) else None
        summary["ids"]["unit_id"] = unit_id

        for code, name, slot in [("A", "Live Onboarding", "department_a_id"), ("B", "Live Ops", "department_b_id"), ("C", "Live Programs", "department_c_id")]:
            s, b, r = call(
                "POST",
                "/v1/workforce/departments",
                cid=lifecycle_cid,
                json_body={
                    "organization_id": org_id,
                    "unit_id": unit_id,
                    "name": name,
                    "code": f"LD{code}-{run_id[-6:]}",
                    "default_roles": ["analyst"] if code == "A" else ["operations_specialist"],
                    "status": "active",
                },
                note=f"phase1 create department {code}",
            )
            p1.append(r)
            if s in (200, 201):
                summary["ids"][slot] = b.get("id")

        dept_a = summary["ids"].get("department_a_id")
        dept_b = summary["ids"].get("department_b_id")
        dept_c = summary["ids"].get("department_c_id")

        s, b, r = call(
            "POST",
            "/v1/workforce/employees",
            cid=lifecycle_cid,
            json_body={
                "organization_id": org_id,
                "department_id": dept_a,
                "workforce_type": "employee",
                "role": "analyst",
                "display_name": f"Live Capture User {run_id[-4:]}",
                "email": f"live.capture.{run_id[-6:]}@tenant-client-01.local",
                "lifecycle_state": "draft",
                "source_system": "sampada",
            },
            note="phase1 create employee",
        )
        p1.append(r)
        if s in (200, 201):
            emp_id = b.get("id")
            wf_ref = b.get("workforce_ref_id")
            summary["ids"]["employee_id"] = emp_id
            summary["ids"]["workforce_ref_id"] = wf_ref

        for path, body, note in [
            (f"/v1/workforce/employees/{emp_id}/lifecycle/onboard", {"reason": "Live onboarding start"}, "phase1 onboard"),
            (f"/v1/workforce/employees/{emp_id}/lifecycle/onboard-complete", {"reason": "Live onboarding complete"}, "phase1 onboard complete"),
            (f"/v1/workforce/employees/{emp_id}/lifecycle/department-transfer", {"new_department_id": dept_b, "reason": "Live transfer"}, "phase1 transfer"),
            (f"/v1/workforce/employees/{emp_id}/lifecycle/role-move", {"new_role": "operations_manager", "transition_type": "promotion", "reason": "Live promotion"}, "phase1 promotion"),
            (f"/v1/workforce/employees/{emp_id}/lifecycle/department-transfer", {"new_department_id": dept_c, "reason": "Live move"}, "phase1 move"),
            (f"/v1/workforce/employees/{emp_id}/lifecycle/offboard-prepare", {"reason": "Live offboard prep"}, "phase1 offboard prepare"),
        ]:
            s, b, r = call("POST", path, cid=lifecycle_cid, json_body=body, note=note)
            p1.append(r)

        s, b, r = call("GET", f"/v1/workforce/trace-replay?correlation_id={lifecycle_cid}", note="phase1 replay")
        p1.append(r)
        summary["phases"]["phase1_workforce"] = {
            "call_count": len(p1),
            "trace_replay_status": s,
            "trace_event_count": (b or {}).get("event_count"),
            "records": p1,
        }

        p3: list[dict[str, Any]] = []
        scenario_cid = str(uuid.uuid4())
        summary["ids"]["governance_correlation_id"] = scenario_cid
        s, b, r = call("POST", "/v1/policies/definitions", json_body={"policy_key": f"leave_policy_live_{run_id[-6:]}", "name": "Leave Policy Live", "description": "Live capture policy", "version": "1.0.0", "rules": {"min_tenure_days": 90, "effect": "observe"}, "scope_type": "tenant"}, note="phase3 create policy")
        p3.append(r)
        policy_key = f"leave_policy_live_{run_id[-6:]}"
        s, b, r = call("POST", "/v1/policies/evaluate", cid=scenario_cid, json_body={"policy_key": policy_key, "context": {"tenure_days": 10}}, note="phase3 evaluate policy")
        p3.append(r)
        eval_id = b.get("evaluation_id") if isinstance(b, dict) else None
        s, b, r = call("POST", "/v1/governance/challenges", cid=scenario_cid, json_body={"policy_key": policy_key, "evaluation_id": eval_id, "subject_type": "policy_evaluation", "subject_id": eval_id, "reason": "Live governance challenge"}, note="phase3 create challenge")
        p3.append(r)
        challenge_id = b.get("challenge_id") if isinstance(b, dict) else None
        s, b, r = call("POST", "/v1/governance/reviews", cid=scenario_cid, json_body={"challenge_id": challenge_id, "reviewer_role": "admin", "notes": "Live review"}, note="phase3 create review")
        p3.append(r)
        review_id = b.get("review_id") if isinstance(b, dict) else None
        s, b, r = call("POST", f"/v1/governance/reviews/{review_id}/complete", json_body={"outcome": "upheld", "notes": "Live review complete"}, note="phase3 complete review")
        p3.append(r)
        s, b, r = call("POST", "/v1/governance/overrides", cid=scenario_cid, json_body={"challenge_id": challenge_id, "policy_key": policy_key, "reason": "Live override", "override_effect": "allow"}, note="phase3 create override")
        p3.append(r)
        override_id = b.get("override_id") if isinstance(b, dict) else None
        s, b, r = call("POST", f"/v1/governance/overrides/{override_id}/apply", note="phase3 apply override")
        p3.append(r)
        s, b, r = call("POST", "/v1/decisions", cid=scenario_cid, json_body={"owner": "Rishabh Yadav", "scope": "tenant", "rationale": "Live capture decision", "inputs": {"evaluation_id": eval_id, "override_id": override_id}, "challenge_id": challenge_id, "review_id": review_id, "trace_references": [scenario_cid]}, note="phase3 create decision")
        p3.append(r)
        decision_id = b.get("decision_id") if isinstance(b, dict) else None
        summary["ids"]["decision_id"] = decision_id
        s, b, r = call("GET", f"/v1/decisions/replay?decision_id={decision_id}", note="phase3 replay decision")
        p3.append(r)
        summary["phases"]["phase3_governance"] = {"call_count": len(p3), "records": p3}

        p5: list[dict[str, Any]] = []
        signal_specs = [
            ("niyantran_telemetry", {"event": "task_completed", "task_id": f"live-{run_id[-4:]}", "workforce_ref": wf_ref}, "observed", True),
            ("artha_payroll_visibility", {"period": "2026-07", "visibility": "summary_only", "workforce_ref": wf_ref}, "observed", False),
            ("crm_participation", {"interaction": "live_touchpoint", "account": "TENANT-CLIENT-01"}, "observed", False),
            ("setu_aggregation", {"aggregate": "cross_system_rollup", "sources": ["niyantran", "artha", "crm"]}, "derived", False),
        ]
        signal_ids = []
        for stype, payload, trust, linked in signal_specs:
            body = {
                "payload": payload,
                "workforce_ref_id": wf_ref,
                "source_declaration": f"{stype} participation",
                "trust_classification": trust,
                "visibility_scope": "tenant",
            }
            if linked:
                body["correlation_id"] = lifecycle_cid
                body["trace_id"] = lifecycle_cid
            s, b, r = call("POST", f"/v1/setu/signals/{stype}", json_body=body, note=f"phase5 ingest {stype}")
            p5.append(r)
            trace_id = (b.get("lineage") or {}).get("trace_id") if isinstance(b, dict) else None
            corr = (b.get("lineage") or {}).get("correlation_id") if isinstance(b, dict) else None
            sig_id = b.get("signal_id") if isinstance(b, dict) else None
            signal_ids.append({"signal_type": stype, "signal_id": sig_id, "trace_id": trace_id, "status": s})
            s2, b2, r2 = call("GET", f"/v1/setu/signals?signal_type={stype}&correlation_id={corr}", note=f"phase5 list {stype}")
            p5.append(r2)
            s3, b3, r3 = call("GET", f"/v1/setu/trace/{trace_id}", note=f"phase5 trace {stype}")
            p5.append(r3)
        summary["ids"]["signal_ids"] = signal_ids
        summary["phases"]["phase5_setu"] = {"call_count": len(p5), "records": p5}

        p7: list[dict[str, Any]] = []
        for path, note in [
            ("/v1/control-center/audit-events?limit=50", "phase7 audit-events all"),
            (f"/v1/control-center/audit-events?correlation_id={lifecycle_cid}", "phase7 audit-events by lifecycle cid"),
            (f"/v1/control-center/audit-replay?correlation_id={lifecycle_cid}", "phase7 audit-replay"),
        ]:
            s, b, r = call("GET", path, note=note)
            p7.append(r)
        summary["phases"]["phase7_control_center"] = {"call_count": len(p7), "records": p7}

    status_counts: dict[str, int] = {}
    for c in captures:
        code = str(c["http_status"])
        status_counts[code] = status_counts.get(code, 0) + 1
    summary["status_counts"] = status_counts
    summary["total_calls"] = len(captures)

    dump_json(run_dir / "capture_index_live.json", summary)
    dump_json(run_dir / "full_capture_live.json", {"captures": captures})
    dump_json(OUT_ROOT / "latest_run.json", {"run_id": run_id, "path": str(run_dir)})

    print("RUN_ID:", run_id)
    print("TOTAL_CALLS:", len(captures))
    print("STATUS_COUNTS:", status_counts)
    print("LIFECYCLE_CID:", lifecycle_cid)
    if summary["blockers"]:
        print("BLOCKERS:", summary["blockers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
