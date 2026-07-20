#!/usr/bin/env python3
"""BHIV Phase IV — production-scale validation harness (load, concurrency, retry)."""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT_ROOT = REPO / "evidence" / "phase_iv_production_validation"


def setup_client():
    os.environ.setdefault("API_KEY_SECRET", "phase-iv-prod-validation-key")
    os.environ.setdefault("JWT_SECRET_KEY", "phase-iv-prod-validation-jwt")
    os.environ.setdefault("CANDIDATE_JWT_SECRET_KEY", "phase-iv-prod-validation-candidate")
    os.environ.setdefault("DATABASE_URL", "mongodb://in-memory.local/bhiv_hr")
    os.environ.setdefault("MONGODB_URI", "mongodb://in-memory.local/bhiv_hr")
    os.environ.setdefault("MONGODB_DB_NAME", "bhiv_hr")

    gateway_root = REPO / "backend" / "services" / "gateway"
    sys.path.insert(0, str(gateway_root))

    from fastapi import FastAPI, Request  # noqa: E402
    from fastapi.testclient import TestClient  # noqa: E402
    from mongomock_motor import AsyncMongoMockClient  # noqa: E402
    import routes.workforce_governance_routes as wroutes  # noqa: E402

    mock_db = AsyncMongoMockClient()["bhiv_hr"]

    async def _get_db_override():
        return mock_db

    wroutes.get_mongo_db = _get_db_override
    app = FastAPI()

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    app.include_router(wroutes.router)
    return TestClient(app), os.environ["API_KEY_SECRET"]


def one_cycle(client, api_key: str, idx: int) -> dict:
    cid = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {api_key}", "X-Correlation-ID": cid}
    started = time.perf_counter()
    org = client.post(
        "/v1/workforce/organizations",
        json={"name": f"Load Org {idx}", "code": f"LO{idx}"},
        headers=headers,
    )
    signal = client.post(
        "/v1/setu/signals/setu_aggregation",
        json={
            "signal_type": "setu_aggregation",
            "payload": {"cycle": idx},
            "source_declaration": "production validation",
            "origin_system": "setu",
            "owning_system": "setu",
            "trace_id": cid,
            "correlation_id": cid,
        },
        headers=headers,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "idx": idx,
        "org_status": org.status_code,
        "signal_status": signal.status_code,
        "latency_ms": elapsed_ms,
        "correlation_id": cid,
    }


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    client, api_key = setup_client()

    # Load test
    cycles = 50
    load_results = [one_cycle(client, api_key, i) for i in range(cycles)]
    latencies = [r["latency_ms"] for r in load_results]
    load_capture = {
        "cycles": cycles,
        "all_org_200": all(r["org_status"] == 200 for r in load_results),
        "all_signal_200": all(r["signal_status"] == 200 for r in load_results),
        "p50_ms": statistics.median(latencies),
        "p95_ms": sorted(latencies)[int(len(latencies) * 0.95) - 1],
        "samples": load_results[:5],
    }

    # Concurrency test
    with ThreadPoolExecutor(max_workers=10) as pool:
        concurrent = list(pool.map(lambda i: one_cycle(client, api_key, 1000 + i), range(20)))
    concurrency_capture = {
        "workers": 10,
        "tasks": 20,
        "success_rate": sum(1 for r in concurrent if r["org_status"] == 200 and r["signal_status"] == 200) / len(concurrent),
        "samples": concurrent[:5],
    }

    # Long-duration (shortened for CI — 30s sustained loop)
    long_started = time.time()
    long_events = []
    while time.time() - long_started < 30:
        long_events.append(one_cycle(client, api_key, 2000 + len(long_events)))
        time.sleep(1)
    long_duration_capture = {
        "duration_seconds": 30,
        "iterations": len(long_events),
        "all_success": all(r["org_status"] == 200 and r["signal_status"] == 200 for r in long_events),
    }

    # Retry behavior — defensive dispatcher return shape (not HA)
    retry_capture = {
        "scenario": "Sampada SETU ingest idempotency via distinct correlation ids",
        "note": "Partner Artha MAX_RETRIES=3 documented in Artha setu.pipeline.js — not executed here (partner repo gitignored)",
        "failover_dr": "UNKNOWN — route to TMS; not simulated in this workspace",
    }

    summary = {
        "run_id": run_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "environment": "in-process FastAPI + mongomock_motor",
        "load": load_capture,
        "concurrency": concurrency_capture,
        "long_duration": long_duration_capture,
        "retry": retry_capture,
    }

    for name, payload in [
        ("load_capture.json", load_capture),
        ("concurrency_capture.json", concurrency_capture),
        ("long_duration_capture.json", long_duration_capture),
        ("retry_capture.json", retry_capture),
        ("capture_index.json", summary),
    ]:
        (run_dir / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    (OUT_ROOT / "latest_run.json").write_text(
        json.dumps({"run_id": run_id, "path": str(run_dir.relative_to(REPO)).replace("\\", "/")}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
