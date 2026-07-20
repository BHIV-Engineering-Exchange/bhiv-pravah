#!/usr/bin/env python3
"""Comprehensive Control Center evaluation against live Render deployment."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None  # type: ignore


def _load_dotenv() -> None:
    backend_root = Path(__file__).resolve().parents[3]
    env_path = backend_root / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def mint_jwt(secret: str, user_id: str, role: str, kind: str = "client") -> str | None:
    if not pyjwt or not secret:
        return None
    now = int(time.time())
    payload: dict = {
        "sub": user_id,
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + 3600,
    }
    if kind == "client":
        payload["client_id"] = user_id
    if kind == "candidate":
        payload["candidate_id"] = user_id
    return pyjwt.encode(payload, secret, algorithm="HS256")


def record(results: list, name: str, passed: bool, detail: str, **meta) -> None:
    results.append({"name": name, "passed": passed, "detail": detail, **meta})


def main() -> int:
    _load_dotenv()

    gateway = os.getenv("GATEWAY_SERVICE_URL", "https://bhiv-hr-gateway-l0xp.onrender.com").rstrip("/")
    agent = os.getenv("AGENT_SERVICE_URL", "https://bhiv-hr-agent-cato.onrender.com").rstrip("/")
    langgraph = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com").rstrip("/")
    api_key = os.getenv("API_KEY_SECRET", "")
    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    cand_jwt = os.getenv("CANDIDATE_JWT_SECRET_KEY", "")
    timeout = float(os.getenv("E2E_HTTP_TIMEOUT", "45"))

    results: list = []
    if not api_key:
        print("BLOCKER: API_KEY_SECRET missing")
        return 1

    api_headers = {"Authorization": f"Bearer {api_key}"}
    correlation_id = str(uuid.uuid4())
    api_headers_cid = {**api_headers, "X-Correlation-ID": correlation_id}

    cc_endpoints = [
        ("GET", "/health", None, False),
        ("GET", "/metrics/dashboard", None, True),
        ("GET", "/v1/candidates/stats", None, True),
        ("GET", "/v1/control-center/dashboard-aggregates", None, True),
        ("GET", "/v1/control-center/audit-events", {"limit": 10}, True),
        ("GET", "/v1/control-center/audit-replay", None, True),
    ]

    gov_endpoints = [
        ("GET", "/v1/workforce/organizations", None),
        ("GET", "/v1/policies/definitions", None),
        ("GET", "/v1/governance/challenges", None),
        ("GET", "/v1/decisions", None),
        ("GET", "/v1/setu/signals", None),
        ("GET", "/v1/workforce/trace-replay", None),
    ]

    with httpx.Client(timeout=timeout) as client:
        for label, base in [("gateway", gateway), ("agent", agent), ("langgraph", langgraph)]:
            try:
                response = client.get(f"{base}/health")
                record(results, f"health_{label}", response.status_code == 200, f"status={response.status_code}")
            except Exception as exc:
                record(results, f"health_{label}", False, str(exc)[:120])

        response = client.get(f"{gateway}/metrics/dashboard")
        record(results, "unauth_metrics_401", response.status_code in (401, 403), f"status={response.status_code}")

        for method, path, params, auth_required in cc_endpoints:
            headers = api_headers_cid if auth_required else {}
            response = client.request(method, f"{gateway}{path}", headers=headers, params=params)
            body: dict = {}
            try:
                body = response.json() if response.content else {}
            except Exception:
                pass
            extra = ""
            if path == "/metrics/dashboard" and response.status_code == 200:
                extra = f" keys={list(body.keys())[:6]} policy_scope={bool(body.get('policy_scope'))}"
            if path == "/v1/candidates/stats" and response.status_code == 200:
                scope = body.get("policy_scope") or {}
                extra = f" scope={scope.get('scope_label', 'n/a')}"
            if "control-center" in path and response.status_code == 200:
                count = body.get("count", len(body.get("events", body.get("hiring_funnel", []))))
                extra = f" count={count}"
            corr = bool(response.headers.get("x-correlation-id"))
            record(
                results,
                f"apikey_{path.strip('/').replace('/', '_')}",
                response.status_code == 200,
                f"status={response.status_code} corr={corr}{extra}",
            )

        write_cid = str(uuid.uuid4())
        response = client.post(
            f"{gateway}/v1/control-center/audit-events",
            headers={**api_headers, "X-Correlation-ID": write_cid},
            json={
                "action": "control_center_evaluation_test",
                "outcome": "success",
                "detail": "comprehensive evaluation canary",
                "correlation_id": write_cid,
            },
        )
        record(
            results,
            "audit_write_canary",
            response.status_code == 200 and (response.json() or {}).get("ok") is True,
            f"status={response.status_code}",
        )

        response = client.get(
            f"{gateway}/v1/control-center/audit-replay",
            headers=api_headers,
            params={"correlation_id": write_cid},
        )
        replay_body = response.json() if response.status_code == 200 else {}
        record(
            results,
            "audit_replay_by_cid",
            response.status_code == 200,
            f"status={response.status_code} events={replay_body.get('count', 0)} mode={replay_body.get('replay_mode')}",
        )

        for method, path, params in gov_endpoints:
            response = client.request(method, f"{gateway}{path}", headers=api_headers, params=params)
            body = response.json() if response.status_code == 200 and response.content else {}
            items = body.get("items", body.get("events", []))
            scope_label = (body.get("policy_scope") or {}).get("scope_label", "n/a")
            item_count = len(items) if isinstance(items, list) else "n/a"
            record(
                results,
                f"gov_{path.strip('/').replace('/', '_')}",
                response.status_code == 200,
                f"status={response.status_code} items={item_count} scope={scope_label}",
            )

        role_cases: list[tuple[str, str | None, int]] = []
        if jwt_secret:
            role_cases.append(("admin_jwt", mint_jwt(jwt_secret, "eval-admin", "admin"), 200))
            role_cases.append(("client_jwt", mint_jwt(jwt_secret, "eval-client-001", "client"), 200))
        if cand_jwt:
            role_cases.append(
                ("recruiter_jwt", mint_jwt(cand_jwt, "eval-recruiter-001", "recruiter", "candidate"), 200)
            )
            role_cases.append(
                ("candidate_jwt", mint_jwt(cand_jwt, "eval-candidate-001", "candidate", "candidate"), 403)
            )

        for name, token, expected in role_cases:
            if not token:
                record(results, f"rbac_{name}", True, "skipped: cannot mint", skipped=True)
                continue
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get(f"{gateway}/v1/candidates/stats", headers=headers)
            body = response.json() if response.content else {}
            scope = (body.get("policy_scope") or {}).get("scope", "n/a")
            passed = response.status_code == expected
            if expected == 200:
                passed = passed and scope in ("client", "recruiter", "platform")
            record(
                results,
                f"rbac_{name}_stats",
                passed,
                f"status={response.status_code} expected={expected} scope={scope}",
            )

            response = client.get(f"{gateway}/metrics/dashboard", headers=headers)
            record(
                results,
                f"rbac_{name}_metrics",
                response.status_code == expected,
                f"status={response.status_code} expected={expected}",
            )

            response = client.get(f"{gateway}/v1/governance/challenges", headers=headers)
            record(
                results,
                f"rbac_{name}_governance",
                response.status_code == expected,
                f"status={response.status_code} expected={expected}",
            )

        client_tok = mint_jwt(jwt_secret, "iso-client-A", "client") if jwt_secret else None
        recruiter_tok = mint_jwt(cand_jwt, "iso-recruiter-B", "recruiter", "candidate") if cand_jwt else None
        if client_tok and recruiter_tok:
            rc = client.get(f"{gateway}/v1/candidates/stats", headers={"Authorization": f"Bearer {client_tok}"})
            rr = client.get(f"{gateway}/v1/candidates/stats", headers={"Authorization": f"Bearer {recruiter_tok}"})
            bc = rc.json() if rc.status_code == 200 else {}
            br = rr.json() if rr.status_code == 200 else {}
            sc = (bc.get("policy_scope") or {}).get("scope")
            sr = (br.get("policy_scope") or {}).get("scope")
            isolated = sc == "client" and sr == "recruiter" and sc != sr
            record(results, "isolation_client_vs_recruiter_scope", isolated, f"client_scope={sc} recruiter_scope={sr}")

        for url in ["https://infiverse-hr.vercel.app", "https://sampada.blackholeinfiverse.com"]:
            host = url.split("//")[1].split("/")[0]
            try:
                page = client.get(url, follow_redirects=True)
                html = page.text or ""
                js_urls = []
                for chunk in html.split('src="'):
                    if chunk.startswith("/assets/") and ".js" in chunk:
                        js_urls.append(chunk.split('"')[0])
                render_host = "bhiv-hr-gateway-l0xp.onrender.com"
                found = False
                for rel in js_urls[:5]:
                    bundle = client.get(f"{url.rstrip('/')}{rel}")
                    if bundle.status_code == 200 and render_host in bundle.text:
                        found = True
                        break
                record(
                    results,
                    f"vercel_{host}",
                    page.status_code == 200,
                    f"status={page.status_code} render_in_bundle={found}",
                )
            except Exception as exc:
                record(results, f"vercel_{host}", False, str(exc)[:120])

    passed = sum(1 for row in results if row["passed"])
    failed = sum(1 for row in results if not row["passed"] and not row.get("skipped"))
    skipped = sum(1 for row in results if row.get("skipped"))

    report = {
        "suite": "control_center_comprehensive_evaluation",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "gateway": gateway,
        "summary": {"total": len(results), "passed": passed, "failed": failed, "skipped": skipped},
        "tests": results,
    }

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "control_center_comprehensive_evaluation_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Results: {passed}/{len(results)} passed, {failed} failed, {skipped} skipped")
    for row in results:
        mark = "SKIP" if row.get("skipped") else ("PASS" if row["passed"] else "FAIL")
        print(f"  [{mark}] {row['name']}: {row['detail']}")
    print(f"Report: {out_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
