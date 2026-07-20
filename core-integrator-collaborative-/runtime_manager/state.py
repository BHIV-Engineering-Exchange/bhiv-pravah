"""Shared runtime status file helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

STATE_DIR = Path(__file__).resolve().parent / "state"
STATUS_FILE = STATE_DIR / "runtime_status.json"


def write_status(payload: Dict[str, Any]) -> None:
    """Persist runtime status snapshot atomically."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    materialized = {"generated_at": datetime.now(timezone.utc).isoformat(), **payload}
    tmp = STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(materialized, indent=2), encoding="utf-8")
    tmp.replace(STATUS_FILE)


def read_status() -> Dict[str, Any]:
    """Read runtime status snapshot if present."""
    if not STATUS_FILE.exists():
        return {
            "generated_at": None,
            "services": {},
            "uptime_seconds": 0.0,
            "shutting_down": False,
        }
    return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
