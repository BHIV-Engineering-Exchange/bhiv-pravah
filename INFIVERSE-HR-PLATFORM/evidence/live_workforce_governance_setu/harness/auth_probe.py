"""Probe live gateway auth — outputs status codes only, no secrets."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / "backend" / ".env"
BASE = "https://bhiv-hr-gateway-l0xp.onrender.com"


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
    health = httpx.get(f"{BASE}/health", timeout=90)
    results = {"health_status": health.status_code, "auth_probe": {}}
    for name in ("API_KEY_SECRET", "GATEWAY_SECRET_KEY"):
        tok = env.get(name, "")
        r = httpx.get(
            f"{BASE}/v1/setu/signals?limit=1",
            headers={"Authorization": f"Bearer {tok}"},
            timeout=90,
        )
        results["auth_probe"][name] = {"status": r.status_code, "works": r.status_code == 200}
    print(json.dumps(results))


if __name__ == "__main__":
    main()
