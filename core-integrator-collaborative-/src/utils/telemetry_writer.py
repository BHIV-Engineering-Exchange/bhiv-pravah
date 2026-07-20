"""Append InsightFlow events to the shared bucket telemetry log."""

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_TELEMETRY_PATH = Path("bhiv_bucket") / "insightflow_events.jsonl"


def emit_insightflow_event(event: Dict[str, Any], path: Path = DEFAULT_TELEMETRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
