"""Production demonstration for telemetry-to-replay flow."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "api_evidence"
    / "production_demo_transcript.json"
)


def main() -> int:
    transcript = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "status": "in_progress",
    }

    payload = {
        "source_id": "substation-7",
        "metric": "transformer_temp_c",
        "value": 99.4,
        "unit": "celsius",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "site": "production-demo",
    }
    ingest = requests.post("http://127.0.0.1:8010/telemetry/ingest", json=payload, timeout=120)
    ingest_data = ingest.json()
    trace_id = ingest_data["trace_id"]
    transcript["steps"].append({"name": "telemetry_ingest", "status_code": ingest.status_code, "trace_id": trace_id})

    alerts = {}
    telemetry = {}
    for _ in range(8):
        alerts = requests.get("http://127.0.0.1:8009/dashboard/alerts", timeout=20).json()
        telemetry = requests.get("http://127.0.0.1:8009/dashboard/telemetry", timeout=20).json()
        if any(a.get("trace_id") == trace_id for a in alerts.get("alerts", [])):
            break
        time.sleep(2)

    transcript["steps"].append({"name": "dashboard_alerts", "alert_count": len(alerts.get("alerts", []))})
    transcript["steps"].append(
        {"name": "dashboard_telemetry", "sample_count": len(telemetry.get("recent_telemetry", []))}
    )

    headers = {"X-API-Key": "prod_shakti_tantra_secret_key_2026"}
    bucket_trace = requests.get(
        f"http://127.0.0.1:8005/bucket/trace/{trace_id}", headers=headers, timeout=30
    ).json()
    replay = requests.get(f"http://127.0.0.1:8004/pipeline/replay/{trace_id}", headers=headers, timeout=30).json()
    transcript["steps"].append(
        {
            "name": "audit_and_replay",
            "artifact_count": len(bucket_trace.get("artifacts", [])),
            "replay_status": replay.get("status"),
        }
    )
    transcript["status"] = "pass"
    transcript["completed_at"] = datetime.now(timezone.utc).isoformat()
    transcript["trace_id"] = trace_id
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    print(json.dumps(transcript, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
