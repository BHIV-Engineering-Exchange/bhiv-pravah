"""Verify runtime_manager shutdown behavior and store evidence JSON."""

from __future__ import annotations

import json
import os
import signal
import socket
import time
from datetime import datetime, timezone
from pathlib import Path


def probe_ports(ports: list[int]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for port in ports:
        sock = socket.socket()
        sock.settimeout(0.5)
        out[str(port)] = sock.connect_ex(("127.0.0.1", port)) == 0
        sock.close()
    return out


def main() -> int:
    manager_pid = int(os.environ.get("RUNTIME_MANAGER_PID", "0"))
    if not manager_pid:
        raise SystemExit("RUNTIME_MANAGER_PID env var is required")

    ports = [8000, 8001, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010]
    before = probe_ports(ports)
    os.kill(manager_pid, signal.SIGINT)
    time.sleep(10)
    after = probe_ports(ports)

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manager_pid": manager_pid,
        "signal": "SIGINT",
        "before_ports_open": before,
        "after_ports_open": after,
        "all_closed_after": not any(after.values()),
        "note": "SIGINT path tested; Windows taskkill terminate path may bypass signal handlers.",
    }

    out_dir = (
        Path(__file__).resolve().parents[1]
        / "evidence"
        / "runtime_metrics"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"shutdown_verification_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
