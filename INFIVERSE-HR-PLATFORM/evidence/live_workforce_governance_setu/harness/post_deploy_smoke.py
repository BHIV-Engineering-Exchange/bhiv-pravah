#!/usr/bin/env python3
"""Post-deploy smoke test for Sampada + 3 partner backends (2026-07-03)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[3]
ENV_PATH = REPO / "backend" / ".env"

SERVICES = {
    "sampada_gateway": {
        "url": "https://bhiv-hr-gateway-l0xp.onrender.com/health",
        "expect": 200,
    },
    "sampada_agent": {
        "url": "https://bhiv-hr-agent-cato.onrender.com/health",
        "expect": 200,
    },
    "sampada_langgraph": {
        "url": "https://bhiv-hr-langgraph-luy9.onrender.com/health",
        "expect": 200,
    },
    "artha_backend": {
        "url": "https://ai-artha.onrender.com/health",
        "expect": 200,
    },
    "ai_crm_backend": {
        "url": "https://ai-crm-4nje.onrender.com/api/auth/login",
        "method": "POST",
        "json": {"email": "probe@invalid.local", "password": "probe"},
        "expect_any": [400, 401, 404, 422, 500],  # server reachable; not 502/503
        "bad": [502, 503, 0],
    },
    "niyantran_backend": {
        "url": "https://blackholeworkflow.onrender.com/api/health",
        "expect_any": [200, 404],
        "fallback": "https://blackholeworkflow.onrender.com/api/auth/login",
        "fallback_method": "POST",
        "fallback_json": {"email": "probe@invalid.local", "password": "probe"},
    },
}

SETU_BASE = "https://bhiv-hr-gateway-l0xp.onrender.com"
PRIOR_SIGNALS = {
    "artha_payroll_visibility": "sig-9802342a158c",
    "crm_participation": "sig-5ffbd0b0bde4",
    "niyantran_telemetry": "sig-29f9efbb899a",
}
SHARED_CID = "3d0a7d1a-1be8-4267-af5b-8d239ea25049"


def load_api_key() -> str:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("API_KEY_SECRET="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def probe(name: str, cfg: dict) -> dict:
    method = cfg.get("method", "GET").upper()
    try:
        with httpx.Client(timeout=90, follow_redirects=True) as client:
            if method == "POST":
                r = client.post(cfg["url"], json=cfg.get("json", {}))
            else:
                r = client.get(cfg["url"])
            status = r.status_code
            ok = status == cfg.get("expect") if "expect" in cfg else status in cfg.get("expect_any", [])
            if not ok and cfg.get("fallback"):
                fb_method = cfg.get("fallback_method", "GET").upper()
                if fb_method == "POST":
                    r = client.post(cfg["fallback"], json=cfg.get("fallback_json", {}))
                else:
                    r = client.get(cfg["fallback"])
                status = r.status_code
                ok = status in cfg.get("expect_any", [200]) and status not in cfg.get("bad", [502, 503])
                url = cfg["fallback"]
            else:
                url = cfg["url"]
            if cfg.get("bad") and status in cfg["bad"]:
                ok = False
            return {"service": name, "url": url, "status": status, "ok": ok, "body_preview": (r.text or "")[:120]}
    except Exception as e:
        return {"service": name, "url": cfg["url"], "status": 0, "ok": False, "error": str(e)}


def setu_checks(api_key: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    out: dict = {}
    with httpx.Client(timeout=90) as client:
        r = client.get(f"{SETU_BASE}/v1/setu/signals?limit=1", headers=headers)
        out["setu_list_auth"] = {"status": r.status_code, "ok": r.status_code == 200}

        for signal_type, expected_id in PRIOR_SIGNALS.items():
            r2 = client.get(
                f"{SETU_BASE}/v1/setu/signals",
                params={"signal_type": signal_type, "correlation_id": SHARED_CID, "limit": 5},
                headers=headers,
            )
            items = (r2.json().get("items") or []) if r2.content else []
            ids = [i.get("signal_id") for i in items]
            out[f"prior_{signal_type}"] = {
                "status": r2.status_code,
                "count": len(items),
                "expected_id_present": expected_id in ids,
                "signal_ids": ids,
            }
    return out


def main() -> int:
    results = {"health": [probe(n, c) for n, c in SERVICES.items()]}
    key = load_api_key()
    if key:
        results["setu"] = setu_checks(key)
    else:
        results["setu"] = {"error": "API_KEY_SECRET not found in backend/.env"}

    all_ok = all(h["ok"] for h in results["health"])
    if "setu_list_auth" in results.get("setu", {}):
        all_ok = all_ok and results["setu"]["setu_list_auth"]["ok"]

    results["summary"] = {"all_health_ok": all(h["ok"] for h in results["health"]), "pass": all_ok}
    print(json.dumps(results, indent=2))
    return 0 if results["summary"]["all_health_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
