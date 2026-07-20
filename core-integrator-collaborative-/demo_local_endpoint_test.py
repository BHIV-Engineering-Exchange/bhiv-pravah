"""Stop-safe local endpoint validation for all sprint services."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "http://127.0.0.1"
API_KEY = os.getenv("AUTH_API_KEY", "prod_shakti_tantra_secret_key_2026")
HEADERS = {"X-API-Key": API_KEY}
OUT = (
    Path("SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)")
    / "evidence"
    / "validation_runs"
    / "local_endpoint_test_20260710.json"
)

SERVICE_CHECKS = {
    "prompt_runner": f"{BASE}:8003/health",
    "creator_core": f"{BASE}:8000/",
    "bhiv_core": f"{BASE}:8001/system/health",
    "integration_bridge": f"{BASE}:8004/pipeline/health",
    "bucket": f"{BASE}:8005/bucket/stats",
    "cet": f"{BASE}:8006/health",
    "sarathi": f"{BASE}:8007/health",
    "gate": f"{BASE}:8008/health",
    "telemetry": f"{BASE}:8010/health",
    "control_plane": f"{BASE}:8009/health",
}

CONTROL_PLANE_ENDPOINTS = [
    "/health",
    "/metrics",
    "/system/status",
    "/dashboard/executive",
    "/dashboard/operations",
    "/dashboard/alerts",
    "/dashboard/runtime",
    "/dashboard/telemetry",
]


def wait_ready(timeout: int = 120) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        ready = True
        for url in SERVICE_CHECKS.values():
            try:
                resp = requests.get(url, headers=HEADERS, timeout=5)
                if resp.status_code != 200:
                    ready = False
                    break
            except Exception:
                ready = False
                break
        if ready:
            return True
        time.sleep(3)
    return False


def validate_control_plane(endpoint: str, body: dict, status_code: int) -> bool:
    if status_code != 200:
        return False
    if endpoint == "/health":
        return body.get("service") == "control_plane"
    if endpoint == "/system/status":
        return "overall_status" in body and "services" in body
    if endpoint == "/metrics":
        return "active_services" in body and "latency_ms" in body
    if endpoint == "/dashboard/executive":
        return "total_pipeline_executions_today" in body
    if endpoint == "/dashboard/operations":
        return "runtime_services" in body
    if endpoint == "/dashboard/alerts":
        return "alerts" in body
    if endpoint == "/dashboard/runtime":
        return "services" in body
    if endpoint == "/dashboard/telemetry":
        return "recent_telemetry" in body and "classification_breakdown" in body
    return True


def get_json(url: str, timeout: int = 15) -> tuple[int, dict | str, str | None]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.status_code, resp.json(), None
        return resp.status_code, resp.text[:200], None
    except Exception as exc:
        return 0, "", str(exc)


def main() -> int:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "health": [],
        "control_plane": [],
        "telemetry": {},
        "pipeline": {},
        "summary": {},
    }

    print("Waiting for all services...")
    if not wait_ready():
        print("TIMEOUT: not all services became healthy within 120s")
        return 2

    print("=== SERVICE HEALTH ===")
    for name, url in SERVICE_CHECKS.items():
        status_code, body, error = get_json(url)
        ok = status_code == 200 and error is None
        row = {"service": name, "url": url, "status_code": status_code, "ok": ok}
        if error:
            row["error"] = error
        report["health"].append(row)
        label = error or status_code
        print(f"{'OK' if ok else 'FAIL'} {name}: {label}")

    print("\n=== CONTROL PLANE ENDPOINTS ===")
    for endpoint in CONTROL_PLANE_ENDPOINTS:
        status_code, body, error = get_json(f"{BASE}:8009{endpoint}", timeout=30)
        payload = body if isinstance(body, dict) else {}
        ok = error is None and validate_control_plane(endpoint, payload, status_code)
        row = {"endpoint": endpoint, "status_code": status_code, "ok": ok}
        if error:
            row["error"] = error
        report["control_plane"].append(row)
        label = error or status_code
        print(f"{'OK' if ok else 'FAIL'} {endpoint}: {label}")
        time.sleep(1)

    print("\n=== TELEMETRY INGEST ===")
    payload = {
        "source_id": "substation-7",
        "metric": "transformer_temp_c",
        "value": 99.4,
        "unit": "celsius",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "site": "local-endpoint-test",
    }
    ingest = requests.post(f"{BASE}:8010/telemetry/ingest", json=payload, headers=HEADERS, timeout=120)
    ingest_body = ingest.json() if ingest.headers.get("content-type", "").startswith("application/json") else {}
    trace_id = ingest_body.get("trace_id")
    telemetry_ok = ingest.status_code == 200 and bool(trace_id)
    report["telemetry"] = {
        "status_code": ingest.status_code,
        "ok": telemetry_ok,
        "trace_id": trace_id,
        "response_keys": sorted(ingest_body.keys()),
        "error_body": ingest_body if ingest.status_code != 200 else None,
    }
    print(f"{'OK' if telemetry_ok else 'FAIL'} ingest: {ingest.status_code} trace_id={trace_id}")

    dashboard_visible = False
    if trace_id and telemetry_ok:
        for _ in range(10):
            try:
                alerts = requests.get(f"{BASE}:8009/dashboard/alerts", timeout=20).json().get("alerts", [])
                if any(alert.get("trace_id") == trace_id for alert in alerts):
                    dashboard_visible = True
                    break
            except Exception:
                pass
            time.sleep(2)
    report["telemetry"]["dashboard_alert_visible"] = dashboard_visible
    print(f"{'OK' if dashboard_visible else 'WARN'} trace visible on /dashboard/alerts")

    print("\n=== PIPELINE EXECUTE + REPLAY ===")
    trace = f"local_{uuid.uuid4().hex[:10]}"
    pipeline_headers = {
        **HEADERS,
        "X-Trace-Id": trace,
        "X-Workflow-Id": f"wf_{uuid.uuid4().hex[:8]}",
    }
    pipeline_payload = {
        "prompt": "Plan a lesson on algebra fundamentals for grade 8 students",
        "product_context": "gurukul",
    }
    pipeline = requests.post(
        f"{BASE}:8004/pipeline/execute",
        json=pipeline_payload,
        headers=pipeline_headers,
        timeout=90,
    )
    replay = requests.get(f"{BASE}:8004/pipeline/replay/{trace}", headers=pipeline_headers, timeout=30)
    pipeline_ok = pipeline.status_code == 200 and replay.status_code == 200
    report["pipeline"] = {
        "status_code": pipeline.status_code,
        "ok": pipeline_ok,
        "trace_id": trace,
        "replay_status": replay.status_code,
        "replay_ok": replay.status_code == 200,
    }
    print(f"{'OK' if pipeline_ok else 'FAIL'} pipeline={pipeline.status_code} replay={replay.status_code}")

    health_ok = sum(1 for row in report["health"] if row["ok"])
    cp_ok = sum(1 for row in report["control_plane"] if row["ok"])
    report["summary"] = {
        "services_healthy": f"{health_ok}/{len(report['health'])}",
        "control_plane_endpoints_ok": f"{cp_ok}/{len(report['control_plane'])}",
        "telemetry_ok": telemetry_ok,
        "telemetry_on_dashboard": dashboard_visible,
        "pipeline_ok": pipeline_ok,
        "all_pass": (
            health_ok == len(report["health"])
            and cp_ok == len(report["control_plane"])
            and telemetry_ok
            and pipeline_ok
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")
    print(json.dumps(report["summary"], indent=2))
    return 0 if report["summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
