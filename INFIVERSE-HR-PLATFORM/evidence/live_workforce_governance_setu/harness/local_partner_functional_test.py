"""Local SETU partner dispatch functional test — writes results only, no secrets."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[3]
ENV_PATH = REPO / "backend" / ".env"
GATEWAY = os.getenv("LOCAL_GATEWAY_URL", "http://127.0.0.1:8000")
CORRELATION_ID = "local-functional-test-20260704"


def load_env(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def confirm(client: httpx.AsyncClient, headers: dict, signal_type: str) -> dict:
    r = await client.get(
        f"{GATEWAY}/v1/setu/signals",
        params={"signal_type": signal_type, "correlation_id": CORRELATION_ID, "limit": 5},
        headers=headers,
        timeout=30,
    )
    items = (r.json().get("items") or []) if r.content else []
    return {"status": r.status_code, "count": len(items), "signal_ids": [i.get("signal_id") for i in items]}


async def test_crm() -> dict:
    sys.path.insert(0, str(REPO / "ai-crm" / "backend"))
    from setu.sampada_dispatcher import dispatch_to_sampada  # noqa: E402

    base = {
        "execution_id": "exec-local-crm",
        "trace_id": "crm-trace-local",
        "tenant_id": "tenant-local",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "execution_completed",
        "details": {"source": "local_functional_test", "module": "crm"},
    }
    crm = await dispatch_to_sampada(base, correlation_id=CORRELATION_ID)
    logistics = await dispatch_to_sampada(
        {**base, "execution_id": "exec-local-logistics", "trace_id": "logistics-trace-local",
         "details": {"source": "local_functional_test", "module": "logistics"}},
        subsystem="logistics",
        correlation_id=CORRELATION_ID,
    )
    return {"crm": crm, "logistics": logistics}


def test_artha(api_key: str) -> dict:
    script = REPO / "Artha" / "backend" / "scripts" / "sampada_partner_capture.mjs"
    env = os.environ.copy()
    env["SETU_ENABLED"] = "true"
    env["SETU_BASE_URL"] = GATEWAY
    env["SETU_API_KEY"] = api_key
    env["SAMPADA_SETU_CORRELATION_ID"] = CORRELATION_ID
    load_env(REPO / "Artha" / "backend" / ".env")
    env["MONGODB_URI"] = os.environ.get("MONGODB_URI", "")
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
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}


def test_niyantran(api_key: str) -> dict:
    script = REPO / "workflow-blackhole" / "server" / "scripts" / "sampada_partner_capture.cjs"
    env = os.environ.copy()
    env["SAMPADA_SETU_ENABLED"] = "true"
    env["SAMPADA_SETU_BASE_URL"] = GATEWAY
    env["SAMPADA_SETU_API_KEY"] = api_key
    env["SAMPADA_SETU_CORRELATION_ID"] = CORRELATION_ID
    load_env(REPO / "workflow-blackhole" / "server" / ".env")
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
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": out or proc.stderr, "exit_code": proc.returncode}


async def main() -> int:
    load_env(ENV_PATH)
    api_key = os.getenv("API_KEY_SECRET", "")
    if not api_key:
        print(json.dumps({"error": "API_KEY_SECRET missing"}))
        return 1

    os.environ["SAMPADA_SETU_ENABLED"] = "true"
    os.environ["SAMPADA_SETU_BASE_URL"] = GATEWAY
    os.environ["SAMPADA_SETU_API_KEY"] = api_key

    headers = {"Authorization": f"Bearer {api_key}"}
    results: dict = {"gateway": GATEWAY, "correlation_id": CORRELATION_ID, "partners": {}}

    results["partners"]["artha"] = test_artha(api_key)
    results["partners"]["crm_bundle"] = await test_crm()
    results["partners"]["niyantran"] = test_niyantran(api_key)

    async with httpx.AsyncClient() as client:
        results["confirmations"] = {
            "artha_payroll_visibility": await confirm(client, headers, "artha_payroll_visibility"),
            "crm_participation": await confirm(client, headers, "crm_participation"),
            "niyantran_telemetry": await confirm(client, headers, "niyantran_telemetry"),
        }

    out_dir = REPO / "evidence" / "live_workforce_governance_setu" / "local_functional" / "20260704T064800Z"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "local_partner_dispatch.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    summary = {
        "artha_ok": results["partners"]["artha"].get("ok") or results["partners"]["artha"].get("dispatched"),
        "crm_ok": results["partners"]["crm_bundle"]["crm"].get("dispatched"),
        "logistics_ok": results["partners"]["crm_bundle"]["logistics"].get("dispatched"),
        "niyantran_ok": results["partners"]["niyantran"].get("ok") or results["partners"]["niyantran"].get("dispatched"),
        "evidence": str(out_dir.relative_to(REPO)).replace("\\", "/"),
    }
    print(json.dumps({"summary": summary, "confirmations": results["confirmations"]}, indent=2))
    return 0 if all(summary[k] for k in ("artha_ok", "crm_ok", "logistics_ok", "niyantran_ok")) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
