#!/usr/bin/env python3
"""BHIV Phase IV — partner environment checkpoint (names only for secrets)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_keys(path: Path) -> list[str]:
    if not path.exists():
        return []
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.append(line.split("=", 1)[0].strip())
    return sorted(keys)


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def node_version() -> str:
    try:
        return subprocess.check_output(["node", "--version"], text=True, timeout=10).strip()
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {exc}"


def python_version() -> str:
    return sys.version.split()[0]


def partner_checkpoint(name: str, env_path: Path, boot_dir: Path | None, default_port: int) -> dict[str, Any]:
    keys = env_keys(env_path)
    has_mongo = "MONGODB_URI" in keys or "DATABASE_URL" in keys
    has_setu = any(k for k in keys if "SAMPADA_SETU" in k or k.startswith("SETU_"))
    package_json = (boot_dir / "package.json") if boot_dir else None
    can_boot = bool(boot_dir and boot_dir.exists() and package_json and package_json.exists())
    verdict = "boot_candidate" if can_boot and has_mongo else "blocked"
    blockers: list[str] = []
    if not env_path.exists():
        blockers.append(f"{env_path.name} missing")
    if not has_mongo:
        blockers.append("MONGODB_URI not configured in .env key list")
    if not has_setu:
        blockers.append("SAMPADA_SETU_* / SETU_* keys not present in .env key list")
    if not can_boot:
        blockers.append("server entry (package.json) not found")
    return {
        "partner": name,
        "env_path": str(env_path.relative_to(REPO)).replace("\\", "/"),
        "env_keys_present": keys,
        "default_port": default_port,
        "port_available": port_free(default_port),
        "boot_dir": str(boot_dir.relative_to(REPO)).replace("\\", "/") if boot_dir else None,
        "boot_candidate": can_boot,
        "verdict": verdict,
        "blockers": blockers,
    }


def main() -> int:
    out_dir = REPO / "evidence" / "phase_iv_tier1"
    out_dir.mkdir(parents=True, exist_ok=True)

    partners = [
        partner_checkpoint(
            "niyantran",
            REPO / "workflow-blackhole" / "server" / ".env",
            REPO / "workflow-blackhole" / "server",
            5000,
        ),
        partner_checkpoint(
            "artha",
            REPO / "Artha" / "backend" / ".env",
            REPO / "Artha" / "backend",
            4000,
        ),
        partner_checkpoint(
            "crm",
            REPO / "ai-crm" / "backend" / ".env",
            REPO / "ai-crm" / "backend",
            8000,
        ),
        partner_checkpoint(
            "logistics",
            REPO / "ai-crm" / "backend" / ".env",
            REPO / "ai-crm" / "backend",
            8000,
        ),
    ]

    no_dispatcher = [
        {"system": "bucket", "verdict": "no_sampada_dispatcher", "route_to": "GC (authority) / MDU (schema)"},
        {"system": "prana", "verdict": "no_sampada_dispatcher", "route_to": "GC / MDU — posts to Bucket only"},
        {"system": "insightflow", "verdict": "no_sampada_dispatcher", "route_to": "GC / MDU"},
        {"system": "karma", "verdict": "no_sampada_dispatcher", "route_to": "GC / MDU — forwards to InsightFlow via stp_bridge"},
    ]

    payload = {
        "captured_at": now_utc(),
        "phase": "BHIV Phase IV — Tier 1 environment checkpoint",
        "runtime": {"python": python_version(), "node": node_version()},
        "sampada_env_keys": env_keys(REPO / "backend" / ".env"),
        "partners": partners,
        "no_dispatcher_systems": no_dispatcher,
        "tier_policy": (
            "Tier 1 requires partner native server boot + business workflow trigger + dispatcher + Sampada trace. "
            "If boot fails, retain Tier 2 with explicit blocker — do not simulate."
        ),
    }

    path = out_dir / "environment_checkpoint.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(path), "partners": [p["partner"] for p in partners]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
