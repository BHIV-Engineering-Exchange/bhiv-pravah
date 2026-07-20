"""Probe local control center and SETU read endpoints — status codes only."""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / "backend" / ".env"
BASE = os.getenv("LOCAL_GATEWAY_URL", "http://127.0.0.1:8000")


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> None:
    env = load_env(ENV_PATH)
    headers = {"Authorization": f"Bearer {env.get('API_KEY_SECRET', '')}"}
    results: dict[str, object] = {}

    with httpx.Client(timeout=30) as client:
        for label, method, path, params in [
            ("setu_list", "GET", "/v1/setu/signals", {"limit": 3}),
            ("setu_trace", "GET", "/v1/setu/trace/crm-trace-local", {"limit": 5}),
            ("cc_audit_events", "GET", "/v1/control-center/audit-events", {"limit": 5}),
            ("cc_audit_replay", "GET", "/v1/control-center/audit-replay", {"correlation_id": "local-functional-test-20260704"}),
            ("cc_dashboard", "GET", "/v1/control-center/dashboard-aggregates", {}),
        ]:
            r = client.request(method, f"{BASE}{path}", params=params or None, headers=headers)
            body = r.json() if r.content and "application/json" in r.headers.get("content-type", "") else {}
            results[label] = {
                "status": r.status_code,
                "ok": r.status_code == 200,
                "keys": list(body.keys()) if isinstance(body, dict) else None,
            }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
