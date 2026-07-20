"""Control plane service for metrics and dashboard APIs."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from fastapi import FastAPI

from config import ConfigManager

REPO_ROOT = Path(__file__).resolve().parent
SPRINT_DIR = REPO_ROOT / "SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)"
if str(SPRINT_DIR) not in sys.path:
    sys.path.insert(0, str(SPRINT_DIR))

from runtime_manager.state import read_status
from spine.alert_generator import get_alert_ring_buffer

app = FastAPI(title="Control Plane Service", version="1.0.0")

bucket_url = ConfigManager.get_service_url("bucket")
bhiv_core_url = ConfigManager.get_service_url("bhiv_core")
integration_bridge_url = ConfigManager.get_service_url("integration_bridge")
telemetry_url = ConfigManager.get_service_url("telemetry")
api_key = os.getenv("AUTH_API_KEY", "")


def _headers() -> Dict[str, str]:
    return {"X-API-Key": api_key} if api_key else {}


def _safe_get_json(url: str) -> Dict[str, Any]:
    try:
        response = requests.get(url, headers=_headers(), timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return {}
    return {}


def _collect_service_metrics() -> Dict[str, Dict[str, Any]]:
    snapshots = {}
    for name, base in [("integration_bridge", integration_bridge_url), ("telemetry", telemetry_url)]:
        snapshots[name] = _safe_get_json(f"{base}/internal/metrics-snapshot")
    return snapshots


def _alerts_from_bucket(limit: int = 25) -> List[Dict[str, Any]]:
    traces = _safe_get_json(f"{bucket_url}/bucket/traces?limit={limit}").get("traces", [])
    alert_records = []
    for trace in traces[:limit]:
        trace_id = trace.get("trace_id")
        if not trace_id:
            continue
        artifacts = _safe_get_json(f"{bucket_url}/bucket/trace/{trace_id}").get("artifacts", [])
        for artifact in artifacts:
            if artifact.get("artifact_type") == "alert":
                alert_records.append(artifact.get("data", {}))
    alert_records.sort(key=lambda x: x.get("raised_at", ""), reverse=True)
    return alert_records


def _overall_status_from_runtime(runtime: Dict[str, Any]) -> str:
    for service in runtime.get("services", {}).values():
        if service.get("status") in ("unhealthy", "CRASH_LOOPING"):
            return "degraded"
    return "ok"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "control_plane"}


@app.get("/metrics")
async def metrics():
    runtime = read_status()
    service_metrics = _collect_service_metrics()
    flat = [v for v in service_metrics.values() if v]
    req_per_min = sum(v.get("requests_per_minute", 0) for v in flat)
    total_req = sum(v.get("total_requests", 0) for v in flat)
    total_err = sum(v.get("error_requests", 0) for v in flat)
    p50s = [v.get("latency_ms", {}).get("p50", 0) for v in flat]
    p95s = [v.get("latency_ms", {}).get("p95", 0) for v in flat]
    alerts = _alerts_from_bucket(limit=25)
    replay_stats = _safe_get_json(f"{bhiv_core_url}/replay/statistics")
    return {
        "active_services": sum(1 for s in runtime.get("services", {}).values() if s.get("status") == "healthy"),
        "services": runtime.get("services", {}),
        "request_throughput_req_min": req_per_min,
        "error_rate_pct": round((total_err / total_req * 100.0), 3) if total_req else 0.0,
        "latency_ms": {
            "p50": round(sum(p50s) / len(p50s), 3) if p50s else 0.0,
            "p95": round(sum(p95s) / len(p95s), 3) if p95s else 0.0,
        },
        "active_alert_count": len(alerts),
        "replay_queue_depth": replay_stats.get("failed_replays", 0),
        "system_uptime_seconds": runtime.get("uptime_seconds", 0.0),
    }


@app.get("/system/status")
async def system_status():
    runtime = read_status()
    alerts = _alerts_from_bucket(limit=25)
    overall = _overall_status_from_runtime(runtime)
    return {
        "overall_status": overall,
        "services": runtime.get("services", {}),
        "uptime_seconds": runtime.get("uptime_seconds", 0.0),
        "active_alerts": len(alerts),
        "last_replay_check": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/dashboard/executive")
async def dashboard_executive():
    runtime = read_status()
    dashboard = _safe_get_json(f"{bucket_url}/bucket/dashboard")
    alerts = _alerts_from_bucket(limit=25)
    severities = {}
    for alert in alerts:
        sev = alert.get("severity", "unknown")
        severities[sev] = severities.get(sev, 0) + 1
    total_traces = dashboard.get("bucket", {}).get("total_traces", 0)
    return {
        "total_pipeline_executions_today": total_traces,
        "success_rate": None,
        "active_alerts_by_severity": severities,
        "overall_system_status": _overall_status_from_runtime(runtime),
    }


@app.get("/dashboard/operations")
async def dashboard_operations():
    runtime = read_status()
    service_mesh_status = {}
    try:
        from core import get_service_mesh

        service_mesh_status = get_service_mesh().get_service_status()
    except Exception:
        pass
    return {
        "runtime_services": runtime.get("services", {}),
        "service_mesh": service_mesh_status,
    }


@app.get("/dashboard/alerts")
async def dashboard_alerts():
    cache = get_alert_ring_buffer()
    persistent = _alerts_from_bucket(limit=25)
    combined = cache + [a for a in persistent if a.get("alert_id") not in {c.get("alert_id") for c in cache}]
    combined.sort(key=lambda x: x.get("raised_at", ""), reverse=True)
    return {"alerts": combined}


@app.get("/dashboard/runtime")
async def dashboard_runtime():
    return read_status()


@app.get("/dashboard/telemetry")
async def dashboard_telemetry():
    traces = _safe_get_json(f"{bucket_url}/bucket/traces?limit=25").get("traces", [])
    telemetry = []
    classifications = {"nominal": 0, "warning": 0, "critical": 0}
    for trace in traces:
        artifacts = _safe_get_json(f"{bucket_url}/bucket/trace/{trace.get('trace_id')}").get("artifacts", [])
        record = {"trace_id": trace.get("trace_id"), "telemetry": None, "signal": None}
        for artifact in artifacts:
            if artifact.get("artifact_type") == "telemetry":
                record["telemetry"] = artifact.get("data")
            if artifact.get("artifact_type") == "alert":
                signal = artifact.get("data", {}).get("signal")
                record["signal"] = signal
                if signal and signal.get("classification") in classifications:
                    classifications[signal.get("classification")] += 1
        if record["telemetry"] or record["signal"]:
            telemetry.append(record)
    telemetry.sort(key=lambda x: (x.get("telemetry") or {}).get("timestamp", ""), reverse=True)
    return {"recent_telemetry": telemetry[:50], "classification_breakdown": classifications}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009)
