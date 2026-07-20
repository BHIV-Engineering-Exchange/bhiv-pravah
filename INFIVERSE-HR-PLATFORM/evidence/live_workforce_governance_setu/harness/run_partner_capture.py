#!/usr/bin/env python3
"""Partner-initiated live SETU capture — writes to partner_live/<UTC>/ (2026-07-02 closeout)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

REPO = Path(__file__).resolve().parents[3]
SAMPADA_ENV = REPO / "backend" / ".env"
OUT_ROOT = REPO / "evidence" / "live_workforce_governance_setu" / "partner_live"
SHARED_CID = "3d0a7d1a-1be8-4267-af5b-8d239ea25049"
GATEWAY = "https://bhiv-hr-gateway-l0xp.onrender.com"


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


async def confirm_signal(client: httpx.AsyncClient, headers: dict, signal_type: str, correlation_id: str) -> dict:
    r = await client.get(
        f"{GATEWAY}/v1/setu/signals",
        params={"signal_type": signal_type, "correlation_id": correlation_id, "limit": 5},
        headers=headers,
        timeout=60,
    )
    body = r.json() if r.content else {}
    items = body.get("items") or []
    return {"status": r.status_code, "count": len(items), "items": items}


async def capture_crm(headers: dict, run_dir: Path, correlation_id: str) -> dict:
    sys.path.insert(0, str(REPO / "ai-crm" / "backend"))
    from setu.sampada_dispatcher import dispatch_to_sampada  # noqa: E402

    base_event = {
        "execution_id": "exec-crm-closeout-20260702",
        "trace_id": f"crm-trace-{correlation_id[:8]}",
        "tenant_id": "tenant-crm-closeout",
        "timestamp": now_utc(),
        "event_type": "execution_completed",
        "details": {"source": "partner_closeout_harness", "module": "crm"},
    }
    crm_result = await dispatch_to_sampada(base_event, correlation_id=correlation_id)
    dump(run_dir / "crm_participation_capture.json", crm_result)

    logistics_event = {
        **base_event,
        "execution_id": "exec-logistics-closeout-20260702",
        "trace_id": f"logistics-trace-{correlation_id[:8]}",
        "details": {"source": "partner_closeout_harness", "module": "logistics", "page": "Logistics.jsx"},
    }
    logistics_result = await dispatch_to_sampada(
        logistics_event, subsystem="logistics", correlation_id=correlation_id
    )
    dump(run_dir / "logistics_crm_participation_capture.json", logistics_result)

    async with httpx.AsyncClient() as client:
        confirm = await confirm_signal(client, headers, "crm_participation", correlation_id)
    dump(run_dir / "crm_participation_confirm.json", confirm)
    return {
        "crm": crm_result,
        "logistics": logistics_result,
        "confirm": confirm,
        "tier": "Tier 2 — dispatcher invoked directly, partner server not booted in this environment",
    }


def capture_artha(run_dir: Path, api_key: str, correlation_id: str) -> dict:
    script = REPO / "Artha" / "backend" / "scripts" / "sampada_partner_capture.mjs"
    env = os.environ.copy()
    env["SETU_ENABLED"] = "true"
    env["SETU_BASE_URL"] = GATEWAY
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
        timeout=120,
        check=False,
    )
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        result = {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}
    dump(run_dir / "artha_payroll_visibility_capture.json", result)
    return result


def _read_env_value(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def capture_niyantran(run_dir: Path, api_key: str, correlation_id: str) -> dict:
    script = REPO / "workflow-blackhole" / "server" / "scripts" / "sampada_partner_capture.cjs"
    env = os.environ.copy()
    env["SAMPADA_SETU_ENABLED"] = "true"
    env["SAMPADA_SETU_BASE_URL"] = GATEWAY
    env["SAMPADA_SETU_API_KEY"] = api_key
    env["SAMPADA_SETU_CORRELATION_ID"] = correlation_id
    env["MONGODB_URI"] = _read_env_value(REPO / "workflow-blackhole" / "server" / ".env", "MONGODB_URI")
    proc = subprocess.run(
        ["node", str(script)],
        cwd=str(REPO / "workflow-blackhole" / "server"),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        result = {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}
    dump(run_dir / "niyantran_telemetry_capture.json", result)
    return result


async def main() -> int:
    load_env(SAMPADA_ENV)
    api_key = os.getenv("API_KEY_SECRET", "")
    if not api_key:
        print("BLOCKER: API_KEY_SECRET missing")
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    headers = {"Authorization": f"Bearer {api_key}"}
    auth_probe = subprocess.check_output([sys.executable, str(REPO / "evidence" / "live_workforce_governance_setu" / "harness" / "auth_probe.py")], text=True)
    auth_data = json.loads(auth_probe)
    dump(run_dir / "auth_probe.json", auth_data)

    boot = {
        "repo_topology": "No uploaded ZIP copies present; embedded copies at Artha/, ai-crm/, workflow-blackhole/ used.",
        "artha_db_configured": bool((REPO / "Artha" / "backend" / ".env").exists()),
        "crm_db_configured": bool((REPO / "ai-crm" / "backend" / ".env").exists()),
        "niyantran_db_configured": bool((REPO / "workflow-blackhole" / "server" / ".env").exists()),
        "tier_decision": {
            "artha": "Tier 2 — dispatcher invoked directly against live gateway; Artha API server not started (JWT-gated dispatch route).",
            "crm": "Tier 2 — sampada_dispatcher invoked directly; CRM FastAPI server not started.",
            "niyantran": "Tier 2 — setuDispatcher invoked with real ExecutionEvent from Niyantran Mongo when available, else blocker recorded.",
            "logistics": "Tier 2 — crm_participation with payload.subsystem=logistics via CRM dispatcher (no separate Logistics backend).",
        },
    }
    dump(run_dir / "environment_checkpoint.json", boot)

    os.environ["SAMPADA_SETU_ENABLED"] = "true"
    os.environ["SAMPADA_SETU_BASE_URL"] = GATEWAY
    os.environ["SAMPADA_SETU_API_KEY"] = api_key

    artha = capture_artha(run_dir, api_key, SHARED_CID)
    crm_bundle = await capture_crm(headers, run_dir, SHARED_CID)
    niyantran = capture_niyantran(run_dir, api_key, SHARED_CID)

    async with httpx.AsyncClient() as client:
        artha_confirm = await confirm_signal(client, headers, "artha_payroll_visibility", SHARED_CID)
        niyantran_confirm = await confirm_signal(client, headers, "niyantran_telemetry", SHARED_CID)
    dump(run_dir / "artha_payroll_visibility_confirm.json", artha_confirm)
    dump(run_dir / "niyantran_telemetry_confirm.json", niyantran_confirm)

    summary = {
        "run_id": run_id,
        "captured_at": now_utc(),
        "gateway": GATEWAY,
        "auth_working_key": "API_KEY_SECRET",
        "shared_correlation_id": SHARED_CID,
        "partners": {
            "artha": artha,
            "crm": crm_bundle["crm"],
            "logistics": crm_bundle["logistics"],
            "niyantran": niyantran,
        },
        "confirmations": {
            "artha": artha_confirm,
            "crm": crm_bundle["confirm"],
            "niyantran": niyantran_confirm,
        },
        "boot_checkpoint": boot,
    }
    dump(run_dir / "capture_index_partner_live.json", summary)

    lines = [
        f"# Partner-initiated live SETU capture — {run_id}",
        "",
        f"- Gateway: `{GATEWAY}`",
        f"- Auth: `API_KEY_SECRET` (Bearer) — `GATEWAY_SECRET_KEY` returned 401",
        f"- Shared correlation_id: `{SHARED_CID}`",
        "",
        "## Per-partner",
    ]
    for name, tier in boot["tier_decision"].items():
        lines.append(f"- **{name}**: {tier}")
    (run_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dump(OUT_ROOT / "latest_run.json", {"run_id": run_id, "path": str(run_dir.relative_to(REPO)).replace("\\", "/")})
    print(json.dumps({"run_dir": str(run_dir), "summary": summary}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
