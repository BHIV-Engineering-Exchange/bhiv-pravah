#!/usr/bin/env python3
"""BHIV Phase IV — Tier 1 runtime capture (dual local in-process + live Render confirmation)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

REPO = Path(__file__).resolve().parents[3]
OUT_ROOT = REPO / "evidence" / "phase_iv_tier1"
GATEWAY_LIVE = "https://bhiv-hr-gateway-l0xp.onrender.com"
SAMPADA_ENV = REPO / "backend" / ".env"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _read_env_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def build_local_harness_client():
    """In-process Sampada workforce/SETU router (same pattern as prior sprint harness)."""
    os.environ.setdefault("API_KEY_SECRET", "phase-iv-tier1-harness-api-key")
    os.environ.setdefault("JWT_SECRET_KEY", "phase-iv-tier1-harness-jwt-secret")
    os.environ.setdefault("CANDIDATE_JWT_SECRET_KEY", "phase-iv-tier1-harness-candidate-secret")
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
    return TestClient(app), mock_db


async def confirm_live(client: httpx.AsyncClient, headers: dict, signal_type: str, correlation_id: str) -> dict:
    r = await client.get(
        f"{GATEWAY_LIVE}/v1/setu/signals",
        params={"signal_type": signal_type, "correlation_id": correlation_id, "limit": 5},
        headers=headers,
        timeout=60,
    )
    body = r.json() if r.content else {}
    items = body.get("items") or body if isinstance(body, list) else []
    if isinstance(body, dict) and "items" not in body:
        items = body.get("signals") or []
    return {"status": r.status_code, "count": len(items), "items": items}


def attempt_partner_server_boot(partner: str, boot_dir: Path, port: int) -> dict:
    """Short-lived boot probe — records whether native server can start."""
    if not (boot_dir / "package.json").exists():
        return {"booted": False, "tier": "Tier 2", "blocker": "package.json missing"}
    env = os.environ.copy()
    env["PORT"] = str(port)
    try:
        proc = subprocess.Popen(
            ["node", "start.js"] if (boot_dir / "start.js").exists() else ["node", "index.js"],
            cwd=str(boot_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        proc.wait(timeout=8)
        stderr_tail = ""
        if proc.stderr:
            stderr_tail = (proc.stderr.read() or "")[-500:]
        return {
            "booted": False,
            "tier": "Tier 2",
            "blocker": f"Server process exited (code {proc.returncode}) within boot window",
            "stderr_tail": stderr_tail,
        }
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"booted": True, "tier": "Tier 1_candidate", "note": "Process survived 8s boot window"}
    except Exception as exc:  # noqa: BLE001
        return {"booted": False, "tier": "Tier 2", "blocker": str(exc)}


async def capture_crm(correlation_id: str, base_url: str, api_key: str) -> dict:
    sys.path.insert(0, str(REPO / "ai-crm" / "backend"))
    from setu.sampada_dispatcher import dispatch_to_sampada  # noqa: E402

    os.environ["SAMPADA_SETU_ENABLED"] = "true"
    os.environ["SAMPADA_SETU_BASE_URL"] = base_url
    os.environ["SAMPADA_SETU_API_KEY"] = api_key

    event = {
        "execution_id": f"exec-crm-phaseiv-{correlation_id[:8]}",
        "trace_id": f"crm-trace-{correlation_id[:8]}",
        "tenant_id": "tenant-phaseiv",
        "timestamp": now_utc(),
        "event_type": "execution_completed",
        "details": {"source": "phase_iv_tier1_harness", "module": "crm"},
    }
    crm = await dispatch_to_sampada(event, correlation_id=correlation_id)
    logistics = await dispatch_to_sampada(
        {**event, "execution_id": f"exec-logistics-phaseiv-{correlation_id[:8]}", "trace_id": f"logistics-trace-{correlation_id[:8]}", "details": {"subsystem": "logistics", "page": "Logistics.jsx"}},
        subsystem="logistics",
        correlation_id=correlation_id,
    )
    return {"crm": crm, "logistics": logistics}


def capture_artha(correlation_id: str, base_url: str, api_key: str) -> dict:
    script = REPO / "Artha" / "backend" / "scripts" / "sampada_partner_capture.mjs"
    env = os.environ.copy()
    env["SETU_ENABLED"] = "true"
    env["SETU_BASE_URL"] = base_url
    env["SETU_API_KEY"] = api_key
    env["SAMPADA_SETU_CORRELATION_ID"] = correlation_id
    load_env(REPO / "Artha" / "backend" / ".env")
    env["MONGODB_URI"] = (os.environ.get("MONGODB_URI") or "").strip().strip('"')
    proc = subprocess.run(
        ["node", str(script)],
        cwd=str(REPO / "Artha" / "backend"),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}


def capture_niyantran(correlation_id: str, base_url: str, api_key: str) -> dict:
    script = REPO / "workflow-blackhole" / "server" / "scripts" / "sampada_partner_capture.cjs"
    env = os.environ.copy()
    env["SAMPADA_SETU_ENABLED"] = "true"
    env["SAMPADA_SETU_BASE_URL"] = base_url
    env["SAMPADA_SETU_API_KEY"] = api_key
    env["SAMPADA_SETU_CORRELATION_ID"] = correlation_id
    env["MONGODB_URI"] = _read_env_value(REPO / "workflow-blackhole" / "server" / ".env", "MONGODB_URI")
    proc = subprocess.run(
        ["node", str(script)],
        cwd=str(REPO / "workflow-blackhole" / "server"),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}


def local_setu_ingest(client, api_key: str, signal_type: str, body: dict) -> dict:
    r = client.post(
        f"/v1/setu/signals/{signal_type}",
        json=body,
        headers={"Authorization": f"Bearer {api_key}", "X-Correlation-ID": body.get("correlation_id", "")},
    )
    return {"status": r.status_code, "body": r.json() if r.content else None}


async def main() -> int:
    load_env(SAMPADA_ENV)
    api_key = os.getenv("API_KEY_SECRET", "")
    if not api_key:
        print("BLOCKER: API_KEY_SECRET missing from backend/.env")
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    correlation_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {api_key}"}

    # Environment + boot probes
    subprocess.run([sys.executable, str(REPO / "evidence" / "phase_iv_tier1" / "harness" / "environment_checkpoint.py")], check=False)
    boot_niyantran = attempt_partner_server_boot("niyantran", REPO / "workflow-blackhole" / "server", 5000)
    boot_artha = attempt_partner_server_boot("artha", REPO / "Artha" / "backend", 4000)
    dump(run_dir / "boot_probes.json", {"niyantran": boot_niyantran, "artha": boot_artha})

  # Local in-process gateway
    local_client, _ = build_local_harness_client()
    local_api_key = os.environ["API_KEY_SECRET"]
    local_base = "in-process://local-gateway"

    # Live partner dispatches
    os.environ["SAMPADA_SETU_ENABLED"] = "true"
    os.environ["SAMPADA_SETU_BASE_URL"] = GATEWAY_LIVE
    os.environ["SAMPADA_SETU_API_KEY"] = api_key

    artha_live = capture_artha(correlation_id, GATEWAY_LIVE, api_key)
    crm_live_bundle = await capture_crm(correlation_id, GATEWAY_LIVE, api_key)
    niyantran_live = capture_niyantran(correlation_id, GATEWAY_LIVE, api_key)

    async with httpx.AsyncClient() as client:
        confirms = {
            "artha": await confirm_live(client, headers, "artha_payroll_visibility", correlation_id),
            "crm": await confirm_live(client, headers, "crm_participation", correlation_id),
            "niyantran": await confirm_live(client, headers, "niyantran_telemetry", correlation_id),
        }

    # Local confirmation via in-process ingest sample
    local_sample = local_setu_ingest(
        local_client,
        local_api_key,
        "setu_aggregation",
        {
            "signal_type": "setu_aggregation",
            "payload": {"phase": "IV", "note": "local in-process confirmation"},
            "source_declaration": "phase_iv harness",
            "origin_system": "setu",
            "owning_system": "setu",
            "trace_id": f"local-trace-{correlation_id[:8]}",
            "correlation_id": correlation_id,
        },
    )

    def tier_label(partner: str, boot: dict, dispatch: dict) -> str:
        dispatched = bool(dispatch.get("ok") or dispatch.get("dispatched"))
        if boot.get("booted") and dispatched:
            return "Tier 1 — partner server booted + business workflow dispatch confirmed"
        if dispatched:
            return "Tier 2 — dispatcher invoked directly; partner server not booted through full HTTP business route"
        return f"Not Yet Available — Blocked on {dispatch.get('error') or dispatch.get('blocker') or boot.get('blocker') or 'dispatch failure'}"

    partners = {
        "artha": {"boot": boot_artha, "live_dispatch": artha_live, "live_confirm": confirms["artha"], "tier": tier_label("artha", boot_artha, artha_live)},
        "crm": {"live_dispatch": crm_live_bundle["crm"], "live_confirm": confirms["crm"], "tier": tier_label("crm", {"booted": False}, crm_live_bundle["crm"])},
        "logistics": {"live_dispatch": crm_live_bundle["logistics"], "tier": tier_label("logistics", {"booted": False}, crm_live_bundle["logistics"])},
        "niyantran": {"boot": boot_niyantran, "live_dispatch": niyantran_live, "live_confirm": confirms["niyantran"], "tier": tier_label("niyantran", boot_niyantran, niyantran_live)},
    }

    summary = {
        "run_id": run_id,
        "captured_at": now_utc(),
        "correlation_id": correlation_id,
        "targets": {"live_gateway": GATEWAY_LIVE, "local_gateway": local_base},
        "partners": partners,
        "local_setu_sample": local_sample,
        "no_dispatcher": ["bucket", "prana", "insightflow", "karma"],
    }

    dump(run_dir / "capture_index_tier1.json", summary)
    dump(OUT_ROOT / "latest_run.json", {"run_id": run_id, "path": str(run_dir.relative_to(REPO)).replace("\\", "/")})

    lines = [
        f"# BHIV Phase IV Tier 1 Runtime Capture — {run_id}",
        "",
        f"- **Live gateway**: `{GATEWAY_LIVE}`",
        f"- **Local gateway**: in-process FastAPI harness (mongomock_motor)",
        f"- **Correlation id**: `{correlation_id}`",
        "",
        "## Per-partner tier",
        "",
        "| Partner | Tier | Notes |",
        "|---|---|---|",
    ]
    for name, data in partners.items():
        lines.append(f"| {name} | {data['tier']} | boot probe recorded |")
    lines += [
        "",
        "## No Sampada dispatcher",
        "",
        "Bucket, PRANA, InsightFlow, Karma — **Not evidenced** (no dispatcher code). Route to GC/MDU.",
    ]
    (run_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
