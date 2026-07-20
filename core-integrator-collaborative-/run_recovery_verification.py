"""Recovery verification: BHIV unavailable at execution, restart, replay from Bucket."""

import json
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1"
API_KEY = "prod_shakti_tantra_secret_key_2026"
HEADERS = {"X-API-Key": API_KEY}
REPO = Path(__file__).parent
OUT_DIR = REPO / "SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)/evidence/recovery_evidence"


def pid_on_port(port: int) -> int | None:
    import psutil

    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == port and conn.status == "LISTEN" and conn.pid:
            return conn.pid
    return None


def start_bhiv_core() -> tuple[bool, int | None]:
    from core.service_orchestrator import ServiceOrchestrator

    orch = ServiceOrchestrator()
    if orch._is_service_healthy("bhiv_core"):
        return True, pid_on_port(8001)
    if not orch._start_service("bhiv_core"):
        return False, None
    return orch._wait_for_health("bhiv_core", 30), orch.processes.get("bhiv_core").pid if orch.processes.get("bhiv_core") else None


def wait_healthy(timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(f"{BASE}:8001/", timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def wait_port_free(port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pid_on_port(port) is None:
            return True
        time.sleep(0.5)
    return False


def run_pipeline(trace_id: str, result: dict) -> None:
    workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
    headers = {**HEADERS, "X-Trace-Id": trace_id, "X-Workflow-Id": workflow_id}
    try:
        resp = requests.post(
            f"{BASE}:8004/pipeline/execute",
            json={"prompt": "Plan a lesson on algebra fundamentals for grade 8 students", "product_context": "gurukul"},
            headers=headers,
            timeout=120,
        )
        result.update({"status_code": resp.status_code, "body": resp.text[:800]})
    except Exception as exc:
        result.update({"status_code": "error", "body": str(exc)})


def bucket_types(trace_id: str) -> set:
    resp = requests.get(f"{BASE}:8005/bucket/trace/{trace_id}", headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return set()
    return {a.get("artifact_type") for a in resp.json().get("artifacts", [])}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    trace_id = f"rec_{uuid.uuid4().hex[:10]}"
    pipeline_result: dict = {}

    bhiv_pid = pid_on_port(8001)
    killed = False
    kill_note = ""
    if bhiv_pid:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(bhiv_pid)], check=True, capture_output=True)
            killed = True
            kill_note = f"taskkill /F /PID {bhiv_pid} (pre-execution)"
        except Exception as exc:
            kill_note = str(exc)
    wait_port_free(8001)

    run_pipeline(trace_id, pipeline_result)
    types_after_failure = bucket_types(trace_id)
    clean_failure = pipeline_result.get("status_code") in (500, "error") and "execution" not in types_after_failure

    restarted, new_pid = start_bhiv_core()
    replay_status = bucket_status = None
    artifact_count = 0
    if restarted:
        replay = requests.get(f"{BASE}:8004/pipeline/replay/{trace_id}", headers=HEADERS, timeout=30)
        replay_status = replay.status_code
        bucket = requests.get(f"{BASE}:8005/bucket/trace/{trace_id}", headers=HEADERS, timeout=30)
        bucket_status = bucket.status_code
        if bucket.status_code == 200:
            artifact_count = len(bucket.json().get("artifacts", []))

    interruption = {
        "trace_id": trace_id,
        "bhiv_pid": bhiv_pid,
        "killed_before_execution": killed,
        "kill_command": kill_note,
        "pipeline_status_code": pipeline_result.get("status_code"),
        "pipeline_body_excerpt": pipeline_result.get("body", "")[:500],
        "bucket_artifact_types": sorted(types_after_failure),
        "clean_failure": clean_failure,
    }
    recovery = {
        "bhiv_restarted": restarted,
        "new_bhiv_pid": new_pid,
        "replay_status_code": replay_status,
        "bucket_status_code": bucket_status,
        "bucket_artifact_count": artifact_count,
        "replay_after_restart": replay_status == 200 and artifact_count >= 5,
    }
    runtime_restart = verify_runtime_manager_restart()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "interruption": interruption,
        "recovery": recovery,
        "runtime_manager_restart_scenario": runtime_restart,
        "passed": clean_failure and recovery.get("replay_after_restart") and runtime_restart.get("passed", False),
    }

    (OUT_DIR / "recovery_verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    node_md = f"""# Node Interruption Results

**Supersedes:** prior `04_validation/node_interruption_results.md` (rate-limit only)  
**Generated:** {report['generated_at']}  
**Status:** {'PASS' if report['passed'] else 'PARTIAL'}

## Test

SIGKILL BHIV Core before pipeline execution (`taskkill /F`), run pipeline through CET/Sarathi/Gate, confirm clean failure before A3.

| Field | Value |
|-------|-------|
| Trace ID | `{trace_id}` |
| BHIV PID killed | `{bhiv_pid}` |
| Kill command | `{kill_note}` |
| Pipeline status | `{pipeline_result.get('status_code')}` |
| Bucket types after failure | `{sorted(types_after_failure)}` |
| Clean failure | `{clean_failure}` |

### Pipeline response excerpt

```
{pipeline_result.get('body', '')[:400]}
```
"""
    (OUT_DIR / "node_interruption_results.md").write_text(node_md, encoding="utf-8")

    replay_md = f"""# Replay After Recovery Results

**Supersedes:** prior `04_validation/replay_after_recovery_results.md`  
**Generated:** {report['generated_at']}  
**Status:** {'PASS' if recovery.get('replay_after_restart') else 'PARTIAL'}

## Test

Restart BHIV Core; replay pre-failure trace from Bucket.

| Field | Value |
|-------|-------|
| Trace ID | `{trace_id}` |
| BHIV restarted | `{recovery.get('bhiv_restarted')}` |
| Replay HTTP status | `{recovery.get('replay_status_code')}` |
| Bucket HTTP status | `{recovery.get('bucket_status_code')}` |
| Artifacts recovered | `{recovery.get('bucket_artifact_count')}` |

- **Replay after restart:** {recovery.get('replay_after_restart')}
"""
    (OUT_DIR / "replay_after_recovery_results.md").write_text(replay_md, encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


def verify_runtime_manager_restart() -> dict:
    status_file = REPO / "runtime_manager/state/runtime_status.json"
    if not status_file.exists():
        return {"passed": False, "reason": "runtime_status.json not found"}
    before = json.loads(status_file.read_text(encoding="utf-8"))
    telem = before.get("services", {}).get("telemetry", {})
    control = before.get("services", {}).get("control_plane", {})
    telem_pid = telem.get("pid")
    control_pid = control.get("pid")
    if not telem_pid or not control_pid:
        return {"passed": False, "reason": "telemetry/control_plane not running"}
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(telem_pid)], check=True, capture_output=True)
        subprocess.run(["taskkill", "/F", "/PID", str(control_pid)], check=True, capture_output=True)
    except Exception as exc:
        return {"passed": False, "reason": f"taskkill failed: {exc}"}

    deadline = time.time() + 45
    while time.time() < deadline:
        latest = json.loads(status_file.read_text(encoding="utf-8"))
        t = latest.get("services", {}).get("telemetry", {})
        c = latest.get("services", {}).get("control_plane", {})
        if (
            t.get("status") == "healthy"
            and c.get("status") == "healthy"
            and t.get("restarts", 0) >= telem.get("restarts", 0) + 1
            and c.get("restarts", 0) >= control.get("restarts", 0) + 1
        ):
            return {
                "passed": True,
                "before": {"telemetry": telem, "control_plane": control},
                "after": {"telemetry": t, "control_plane": c},
            }
        time.sleep(2)
    latest = json.loads(status_file.read_text(encoding="utf-8"))
    return {
        "passed": False,
        "reason": "services did not auto-restart within timeout",
        "before": {"telemetry": telem, "control_plane": control},
        "after": {
            "telemetry": latest.get("services", {}).get("telemetry", {}),
            "control_plane": latest.get("services", {}).get("control_plane", {}),
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
