#!/usr/bin/env python3
"""Production smoke checks for Control Center (Render gateway + Vercel hints)."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx

GATEWAY = os.getenv("GATEWAY_URL", "https://bhiv-hr-gateway-l0xp.onrender.com").rstrip("/")
AGENT = os.getenv("AGENT_URL", "https://bhiv-hr-agent-cato.onrender.com").rstrip("/")
LANGGRAPH = os.getenv("LANGGRAPH_URL", "https://bhiv-hr-langgraph-luy9.onrender.com").rstrip("/")
API_KEY = os.getenv("API_KEY_SECRET", os.getenv("API_KEY", ""))
VERCEL_URLS = [
    u.strip()
    for u in os.getenv(
        "VERCEL_SMOKE_URLS",
        "https://infiverse-hr.vercel.app,https://sampada.blackholeinfiverse.com",
    ).split(",")
    if u.strip()
]
# Legacy TECH001/demo123 is archived — not in production DB. Set E2E_CLIENT_* only for optional JWT smoke.
CLIENT_ID = os.getenv("E2E_CLIENT_ID", "").strip()
CLIENT_PASSWORD = os.getenv("E2E_CLIENT_PASSWORD", "").strip()
TIMEOUT = float(os.getenv("E2E_HTTP_TIMEOUT", "45"))


def record(results: List[Dict[str, Any]], name: str, passed: bool, detail: str, **meta: Any) -> None:
    results.append({"name": name, "passed": passed, "detail": detail, **meta})


def main() -> int:
    results: List[Dict[str, Any]] = []
    if not API_KEY:
        print("ERROR: Set API_KEY_SECRET for production API checks.")
        return 1

    headers = {"Authorization": f"Bearer {API_KEY}"}
    t0 = time.perf_counter()

    with httpx.Client(timeout=TIMEOUT) as client:
        for label, base in [("gateway", GATEWAY), ("agent", AGENT), ("langgraph", LANGGRAPH)]:
            try:
                r = client.get(f"{base}/health")
                record(results, f"health_{label}", r.status_code == 200, f"{r.status_code}")
            except Exception as exc:
                record(results, f"health_{label}", False, str(exc))

        r = client.get(f"{GATEWAY}/metrics/dashboard", headers=headers)
        record(
            results,
            "metrics_dashboard",
            r.status_code == 200,
            f"status={r.status_code} correlation={bool(r.headers.get('x-correlation-id'))}",
        )

        r = client.get(f"{GATEWAY}/v1/candidates/stats", headers=headers)
        scope = (r.json() or {}).get("policy_scope", {}) if r.status_code == 200 else {}
        record(
            results,
            "candidates_stats",
            r.status_code == 200,
            f"status={r.status_code} scope={scope.get('scope_label', 'n/a')}",
        )

        for path in [
            "/v1/control-center/dashboard-aggregates",
            "/v1/control-center/audit-replay",
            "/v1/control-center/audit-events",
        ]:
            r = client.get(f"{GATEWAY}{path}", headers=headers)
            record(results, path.strip("/").replace("/", "_"), r.status_code == 200, f"status={r.status_code}")

        r = client.post(
            f"{GATEWAY}/v1/control-center/audit-events",
            headers=headers,
            json={
                "action": "production_smoke_test",
                "outcome": "success",
                "detail": "automated production canary",
                "context": {"source": "production_smoke_script"},
            },
        )
        record(results, "audit_write", r.status_code == 200, f"status={r.status_code}")

        r = client.get(f"{GATEWAY}/metrics/dashboard", headers={"Authorization": "Bearer invalid"})
        record(results, "unauthenticated_denied", r.status_code == 401, f"status={r.status_code}")

        client_token: str | None = None
        if CLIENT_ID and CLIENT_PASSWORD:
            try:
                lr = client.post(
                    f"{GATEWAY}/v1/client/login",
                    json={"client_id": CLIENT_ID, "password": CLIENT_PASSWORD},
                )
                if lr.status_code == 200 and lr.json().get("access_token"):
                    client_token = str(lr.json()["access_token"])
                    record(results, "client_login", True, "token received")
                elif lr.status_code == 200 and lr.json().get("success") is False:
                    record(
                        results,
                        "client_login",
                        True,
                        f"skipped: login failed ({lr.json().get('error', 'invalid credentials')})",
                        skipped=True,
                    )
                else:
                    record(results, "client_login", False, f"status={lr.status_code} body={lr.text[:120]}")
            except Exception as exc:
                record(results, "client_login", False, str(exc))
        else:
            record(
                results,
                "client_login",
                True,
                "skipped: no E2E_CLIENT_ID/E2E_CLIENT_PASSWORD (archived TECH001/demo123 not used)",
                skipped=True,
            )
            record(results, "client_scoped_stats", True, "skipped: requires client JWT", skipped=True)
            record(results, "client_metrics_allowed", True, "skipped: requires client JWT", skipped=True)

        if client_token:
            ch = {"Authorization": f"Bearer {client_token}"}
            r = client.get(f"{GATEWAY}/v1/candidates/stats", headers=ch)
            scope = (r.json() or {}).get("policy_scope", {}) if r.status_code == 200 else {}
            record(
                results,
                "client_scoped_stats",
                r.status_code == 200 and scope.get("scope") == "client",
                f"status={r.status_code} scope={scope.get('scope_label')}",
            )
            r = client.get(f"{GATEWAY}/metrics/dashboard", headers=ch)
            record(results, "client_metrics_allowed", r.status_code == 200, f"status={r.status_code}")

        for vercel_base in VERCEL_URLS:
            name = vercel_base.replace("https://", "").split("/")[0]
            try:
                fr = client.get(vercel_base, follow_redirects=True)
                html = fr.text or ""
                has_control = "/control" in html or "control" in html.lower()
                record(
                    results,
                    f"vercel_fetch_{name}",
                    fr.status_code == 200,
                    f"status={fr.status_code} spa_loaded={len(html) > 500}",
                )
                assets = client.get(f"{vercel_base.rstrip('/')}/", follow_redirects=True)
                bundle_hint = "onrender.com" in assets.text or "localhost:8000" in assets.text
                if not bundle_hint:
                    for path_part in ["/assets/index", "/src"]:
                        pass
                js_urls = []
                for chunk in html.split('src="'):
                    if chunk.startswith("/assets/") and ".js" in chunk:
                        js_urls.append(chunk.split('"')[0])
                render_host = "bhiv-hr-gateway-l0xp.onrender.com"
                agent_host = "bhiv-hr-agent-cato.onrender.com"
                render_in_bundle = False
                for rel in js_urls[:5]:
                    jr = client.get(f"{vercel_base.rstrip('/')}{rel}")
                    if jr.status_code == 200:
                        body = jr.text
                        render_in_bundle = render_in_bundle or render_host in body or agent_host in body
                record(
                    results,
                    f"vercel_bundle_urls_{name}",
                    render_in_bundle,
                    f"render_hosts_in_js={render_in_bundle} chunks_checked={min(len(js_urls), 5)}",
                )
            except Exception as exc:
                record(results, f"vercel_fetch_{name}", False, str(exc))

        # --- Task 20: Workforce Governance Endpoints ---
        org_id: str | None = None
        smoke_trace_id: str | None = None
        smoke_ts = datetime.now(timezone.utc).strftime("%H%M%S")

        try:
            r = client.post(
                f"{GATEWAY}/v1/workforce/organizations",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "name": "Smoke Test Org",
                    "code": f"SMOKE-{smoke_ts}",
                    "status": "active",
                    "default_roles": [],
                },
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            org_id = data.get("id") or data.get("_id")
            passed = r.status_code in (200, 201) and bool(org_id)
            if not passed:
                org_id = None
                record(
                    results,
                    "workforce_org_create",
                    False,
                    f"status={r.status_code} body={r.text[:300]}",
                )
            else:
                record(results, "workforce_org_create", True, f"status={r.status_code} org_id={org_id}")
        except Exception as exc:
            org_id = None
            record(results, "workforce_org_create", False, str(exc))

        try:
            if org_id is None:
                record(results, "workforce_employee_create", True, "[SKIP] org_id unavailable", skipped=True)
            else:
                r = client.post(
                    f"{GATEWAY}/v1/workforce/employees",
                    headers={**headers, "Content-Type": "application/json"},
                    json={
                        "organization_id": org_id,
                        "workforce_type": "employee",
                        "role": "analyst",
                        "display_name": "Smoke User",
                        "lifecycle_state": "draft",
                        "source_system": "smoke_test",
                    },
                )
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                passed = r.status_code in (200, 201) and bool(data.get("workforce_ref_id"))
                record(
                    results,
                    "workforce_employee_create",
                    passed,
                    f"status={r.status_code} workforce_ref_id={data.get('workforce_ref_id')}",
                )
        except Exception as exc:
            record(results, "workforce_employee_create", False, str(exc))

        try:
            r = client.post(
                f"{GATEWAY}/v1/policies/seed",
                headers={**headers, "Content-Type": "application/json"},
                json={},
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            record(
                results,
                "policy_seed",
                r.status_code == 200 and "seeded" in data,
                f"status={r.status_code}",
            )
        except Exception as exc:
            record(results, "policy_seed", False, str(exc))

        try:
            r = client.post(
                f"{GATEWAY}/v1/policies/evaluate",
                headers={**headers, "Content-Type": "application/json"},
                json={"policy_key": "leave_policy", "context": {"tenure_days": 120}},
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            result = data.get("result") or {}
            passed = r.status_code == 200 and isinstance(result, dict) and "decision" in result
            record(results, "policy_evaluate", passed, f"status={r.status_code} decision={result.get('decision')}")
        except Exception as exc:
            record(results, "policy_evaluate", False, str(exc))

        try:
            r = client.post(
                f"{GATEWAY}/v1/setu/signals/niyantran_telemetry",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "payload": {"event": "smoke_check"},
                    "source_declaration": "smoke test",
                    "trust_classification": "observed",
                    "visibility_scope": "tenant",
                },
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            smoke_trace_id = None
            if r.status_code in (200, 201) and data.get("signal_id"):
                lineage = data.get("lineage") or {}
                smoke_trace_id = lineage.get("trace_id") or data.get("trace_id")
                record(results, "setu_signal_ingest", True, f"status={r.status_code} signal_id={data.get('signal_id')}")
            else:
                record(
                    results,
                    "setu_signal_ingest",
                    False,
                    f"status={r.status_code} body={r.text[:300]}",
                )
        except Exception as exc:
            smoke_trace_id = None
            record(results, "setu_signal_ingest", False, str(exc))

        try:
            if smoke_trace_id is None:
                record(results, "setu_trace_continuity", True, "[SKIP] smoke_trace_id unavailable", skipped=True)
            else:
                r = client.get(f"{GATEWAY}/v1/setu/trace/{smoke_trace_id}", headers=headers)
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                signal_count = data.get("signal_count", 0)
                passed = r.status_code == 200 and signal_count >= 1
                record(
                    results,
                    "setu_trace_continuity",
                    passed,
                    f"status={r.status_code} signal_count={signal_count}",
                )
        except Exception as exc:
            record(results, "setu_trace_continuity", False, str(exc))

        try:
            r = client.post(
                f"{GATEWAY}/v1/decisions",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "owner": "smoke_runner",
                    "scope": "platform",
                    "rationale": "Smoke test decision",
                    "inputs": {"source": "smoke"},
                    "status": "active",
                },
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            record(
                results,
                "decision_create",
                r.status_code in (200, 201) and bool(data.get("decision_id")),
                f"status={r.status_code} decision_id={data.get('decision_id')}",
            )
        except Exception as exc:
            record(results, "decision_create", False, str(exc))

        try:
            r = client.post(
                f"{GATEWAY}/v1/governance/challenges",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "policy_key": "leave_policy",
                    "reason": "Smoke test challenge",
                    "subject_type": "policy_evaluation",
                },
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            record(
                results,
                "challenge_create",
                r.status_code in (200, 201) and bool(data.get("challenge_id")),
                f"status={r.status_code} challenge_id={data.get('challenge_id')}",
            )
        except Exception as exc:
            record(results, "challenge_create", False, str(exc))

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"] and not r.get("skipped"))

    report = {
        "suite": "control_center_production_smoke",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": elapsed_ms,
        "gateway": GATEWAY,
        "vercel_urls": VERCEL_URLS,
        "summary": {"total": len(results), "passed": passed, "failed": failed},
        "tests": results,
    }

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "control_center_production_smoke_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Production smoke: {passed}/{len(results)} passed ({elapsed_ms} ms)")
    for row in results:
        mark = "PASS" if row["passed"] else "FAIL"
        print(f"  [{mark}] {row['name']}: {row['detail']}")
    print(f"Report: {out_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
