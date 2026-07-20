"""Determinism verification: same prompt twice + replay hash reconstruction."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1"
API_KEY = "prod_shakti_tantra_secret_key_2026"
HEADERS = {"X-API-Key": API_KEY}
PROMPT = "Design a cooperative dungeon board game with card drafting mechanics"
OUT_MD = Path(
    "Sovereign Runtime Deployment And Ecosystem Operationalization/10_recovery_hardening/determinism_verification.md"
)
OUT_JSON = OUT_MD.with_suffix(".json")


from src.utils.determinism import hash_from_bucket_artifacts


def compute_hash_from_artifacts(artifacts: list) -> str:
    return hash_from_bucket_artifacts(artifacts)


def run_once(trace_id: str) -> dict:
    workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
    headers = {**HEADERS, "X-Trace-Id": trace_id, "X-Workflow-Id": workflow_id}
    resp = requests.post(
        f"{BASE}:8004/pipeline/execute",
        json={"prompt": PROMPT, "product_context": "ttg"},
        headers=headers,
        timeout=90,
    )
    row = {"trace_id": trace_id, "status_code": resp.status_code}
    if resp.status_code != 200:
        row["error"] = resp.text[:500]
        return row
    body = resp.json()
    row["deterministic_hash"] = body.get("pipeline_result", {}).get("deterministic_hash")
    replay = requests.get(f"{BASE}:8004/pipeline/replay/{trace_id}", headers=headers, timeout=30)
    row["replay_status"] = replay.status_code
    bucket = requests.get(f"{BASE}:8005/bucket/trace/{trace_id}", headers=headers, timeout=30)
    row["bucket_status"] = bucket.status_code
    if bucket.status_code == 200:
        artifacts = bucket.json().get("artifacts", [])
        row["reconstructed_hash"] = compute_hash_from_artifacts(artifacts)
        row["stored_hash"] = next(
            (a["data"].get("deterministic_hash") for a in artifacts if a.get("artifact_type") == "result"),
            None,
        )
    return row


def main() -> int:
    trace_a = f"det_{uuid.uuid4().hex[:10]}"
    trace_b = f"det_{uuid.uuid4().hex[:10]}"
    run_a = run_once(trace_a)
    run_b = run_once(trace_b)

    hashes_match = (
        run_a.get("deterministic_hash")
        and run_a.get("deterministic_hash") == run_b.get("deterministic_hash")
    )
    replay_matches = run_a.get("reconstructed_hash") == run_a.get("deterministic_hash")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt": PROMPT,
        "run_a": run_a,
        "run_b": run_b,
        "hashes_match_across_runs": hashes_match,
        "replay_reconstructs_hash": replay_matches,
        "passed": bool(hashes_match and replay_matches and run_a.get("status_code") == 200),
    }

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = f"""# Determinism Verification

**Generated:** {report['generated_at']}  
**Status:** {'PASS' if report['passed'] else 'FAIL'}

## Method

1. Run identical prompt twice through live `/pipeline/execute` (different trace IDs).
2. Compare `deterministic_hash` in both pipeline results.
3. Replay trace A from Bucket; reconstruct hash from stored instruction/blueprint/contract/execution artifacts.

## Runs

| Run | Trace ID | Status | deterministic_hash |
|-----|----------|--------|-------------------|
| A | `{trace_a}` | {run_a.get('status_code')} | `{run_a.get('deterministic_hash', 'n/a')}` |
| B | `{trace_b}` | {run_b.get('status_code')} | `{run_b.get('deterministic_hash', 'n/a')}` |

## Results

- **Hashes match across runs:** {hashes_match}
- **Replay reconstructs hash:** {replay_matches} (reconstructed=`{run_a.get('reconstructed_hash')}`, pipeline=`{run_a.get('deterministic_hash')}`)
- **Bucket trace:** {run_a.get('bucket_status')}
- **Replay endpoint:** {run_a.get('replay_status')}

## Raw JSON

`10_recovery_hardening/determinism_verification.json`
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
