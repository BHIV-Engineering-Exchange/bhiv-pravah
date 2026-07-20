"""Telemetry ingest service for SHAKTI spine."""

import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import ConfigManager
from src.core.failure_handler import FailureHandler
from src.utils.observability import observability_middleware

REPO_ROOT = Path(__file__).resolve().parent
SPRINT_DIR = REPO_ROOT / "SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)"
if str(SPRINT_DIR) not in sys.path:
    sys.path.insert(0, str(SPRINT_DIR))

from runtime_manager.metrics_middleware import request_metrics_middleware, get_local_metrics_snapshot
from spine.alert_generator import generate_alert, push_alert
from spine.signal_generator import generate_signal
from spine.telemetry_schema import validate_telemetry

app = FastAPI(title="Telemetry Service", version="1.0.0")
app.middleware("http")(observability_middleware)
app.middleware("http")(request_metrics_middleware)

failure_handler = FailureHandler()
bucket_url = ConfigManager.get_service_url("bucket")
integration_bridge_url = ConfigManager.get_service_url("integration_bridge")
api_key = os.getenv("AUTH_API_KEY", "")

_autonomous_task = None
_sources = [
    ("substation-7", "transformer_temp_c", "celsius"),
    ("grid-zone-a", "grid_load_mw", "mw"),
    ("feeder-21", "voltage_v", "v"),
]


class TelemetryRequest(BaseModel):
    source_id: str
    metric: str
    value: float
    unit: str
    timestamp: str
    site: str | None = None


async def _ingest_telemetry_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    valid, error_message = validate_telemetry(payload)
    if not valid:
        error = failure_handler.handle_validation_error("telemetry_payload", error_message or "Invalid payload")
        raise HTTPException(status_code=422, detail=error)

    trace_id = payload.get("trace_id") or f"trace_{uuid.uuid4().hex[:12]}"
    artifact_id = f"telemetry_{uuid.uuid4().hex[:8]}"
    headers = {"X-Trace-Id": trace_id}
    if api_key:
        headers["X-API-Key"] = api_key

    telemetry_payload = {
        **payload,
        "trace_id": trace_id,
        "source_module_id": "telemetry_service",
        "status": "success",
        "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }
    store_resp = requests.post(
        f"{bucket_url}/bucket/store",
        json={
            "artifact_id": artifact_id,
            "artifact_type": "telemetry",
            "data": telemetry_payload,
            "trace_id": trace_id,
        },
        headers=headers,
        timeout=20,
    )
    store_resp.raise_for_status()

    signal = generate_signal(telemetry_payload)
    pipeline_resp = requests.post(
        f"{integration_bridge_url}/pipeline/execute",
        json={
            "prompt": signal["prompt"],
            "trace_id": trace_id,
            "product_context": "simulation_runtime",
        },
        headers=headers,
        timeout=120,
    )
    pipeline_resp.raise_for_status()
    pipeline_result = pipeline_resp.json()

    alert = generate_alert(signal, pipeline_result)
    if alert:
        requests.post(
            f"{bucket_url}/bucket/store",
            json={
                "artifact_id": alert["alert_id"],
                "artifact_type": "alert",
                "data": alert,
                "trace_id": trace_id,
            },
            headers=headers,
            timeout=20,
        ).raise_for_status()
        push_alert(alert)

    return {
        "trace_id": trace_id,
        "telemetry_artifact_id": artifact_id,
        "signal": signal,
        "pipeline_result": pipeline_result,
        "alert": alert,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "telemetry"}


@app.get("/internal/metrics-snapshot")
async def internal_metrics_snapshot():
    return get_local_metrics_snapshot()


@app.post("/telemetry/ingest")
async def ingest_telemetry(request: TelemetryRequest):
    return await _ingest_telemetry_event(request.model_dump(exclude_none=True))


async def _autonomous_loop() -> None:
    while True:
        enabled = os.getenv("TELEMETRY_AUTO_ENABLED", "true").lower() in ("1", "true", "yes")
        interval = int(os.getenv("TELEMETRY_AUTO_INTERVAL_SECONDS", "30"))
        if enabled:
            source_id, metric, unit = random.choice(_sources)
            base = {
                "transformer_temp_c": random.uniform(72, 101),
                "grid_load_mw": random.uniform(420, 760),
                "voltage_v": random.uniform(220, 268),
            }[metric]
            payload = {
                "source_id": source_id,
                "metric": metric,
                "value": round(base, 2),
                "unit": unit,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "site": "autonomous-loop",
            }
            try:
                await _ingest_telemetry_event(payload)
            except Exception:
                pass
        await asyncio.sleep(max(5, interval))


@app.on_event("startup")
async def on_startup():
    global _autonomous_task
    _autonomous_task = asyncio.create_task(_autonomous_loop())


@app.on_event("shutdown")
async def on_shutdown():
    if _autonomous_task:
        _autonomous_task.cancel()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
