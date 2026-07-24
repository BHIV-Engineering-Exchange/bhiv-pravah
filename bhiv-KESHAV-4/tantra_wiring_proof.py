"""
PHASE 3 — FULL TANTRA WIRING PROOF

Proves KESHAV operates as a live ecosystem participant in the full TANTRA chain:
  SETU/Input → KESHAV → RAJYA → Sarathi → Core → Bucket → InsightFlow

Six validation dimensions:
  1. Complete flow wiring (chain executes without manual intervention)
  2. Contract compatibility (each layer accepts upstream output)
  3. Trace preservation (trace_id is byte-identical across all layers)
  4. Enforcement propagation (Sarathi + Core correctly act on resolution_signal)
  5. Bucket persistence (truth layer stores and retrieves execution records)
  6. Observability emission (InsightFlow emits correct structured events)

Output: TANTRA_WIRING_PROOF.md
"""

import json
import sys
import textwrap
from datetime import datetime, timezone

# ── Reset shared state before proof run ──────────────────────────────────────
from tantra import bucket, insightflow
bucket.clear()
insightflow.clear()

from tantra.pipeline import run_tantra_pipeline
from tantra import rajya, sarathi, core


def _separator(title: str) -> str:
    return f"\n{'━' * 80}\n## {title}\n{'━' * 80}"


def _json_block(data: dict) -> str:
    return f"```json\n{json.dumps(data, indent=2, sort_keys=True)}\n```"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 1: VALID END-TO-END CHAIN
# ═══════════════════════════════════════════════════════════════════════════════
VALID_INPUT = {
    "trace_id": "tantra-wiring-trace-001",
    "execution_id": "wiring-exec-001",
    "tasks": [
        {"task_id": "T1", "depends_on": []},
        {"task_id": "T2", "depends_on": ["T1"]},
        {"task_id": "T3", "depends_on": ["T2"]},
    ],
    "constraint_results": [
        {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
        {"task_id": "T3", "is_valid": True, "unsatisfied_dependencies": []},
    ],
    "propagation_results": [
        {"task_id": "T1", "affected_tasks": ["T2", "T3"], "impact_score": 10},
        {"task_id": "T2", "affected_tasks": ["T3"], "impact_score": 4},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 2: CORRUPTED INPUT (FAIL-CLOSED)
# ═══════════════════════════════════════════════════════════════════════════════
CORRUPTED_INPUT = {
    "execution_id": "bad-exec-001",
    "tasks": [],
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 3: NO BLOCKED TASKS (CLEAN GRAPH)
# ═══════════════════════════════════════════════════════════════════════════════
CLEAN_INPUT = {
    "trace_id": "tantra-wiring-trace-002",
    "execution_id": "wiring-exec-002",
    "tasks": [
        {"task_id": "A1", "depends_on": []},
        {"task_id": "A2", "depends_on": ["A1"]},
    ],
    "constraint_results": [
        {"task_id": "A1", "is_valid": True, "unsatisfied_dependencies": []},
        {"task_id": "A2", "is_valid": True, "unsatisfied_dependencies": []},
    ],
    "propagation_results": [],
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 4: REPLAY DETERMINISM
# ═══════════════════════════════════════════════════════════════════════════════
REPLAY_INPUT = {
    "trace_id": "tantra-wiring-trace-003",
    "execution_id": "wiring-exec-003",
    "tasks": [
        {"task_id": "R1", "depends_on": []},
        {"task_id": "R2", "depends_on": ["R1"]},
        {"task_id": "R3", "depends_on": ["R1"]},
        {"task_id": "R4", "depends_on": ["R2", "R3"]},
    ],
    "constraint_results": [
        {"task_id": "R1", "is_valid": False, "unsatisfied_dependencies": []},
        {"task_id": "R2", "is_valid": False, "unsatisfied_dependencies": ["R1"]},
        {"task_id": "R3", "is_valid": False, "unsatisfied_dependencies": ["R1"]},
        {"task_id": "R4", "is_valid": False, "unsatisfied_dependencies": ["R2", "R3"]},
    ],
    "propagation_results": [
        {"task_id": "R1", "affected_tasks": ["R2", "R3", "R4"], "impact_score": 15},
        {"task_id": "R2", "affected_tasks": ["R4"], "impact_score": 5},
        {"task_id": "R3", "affected_tasks": ["R4"], "impact_score": 5},
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO 5: PARALLEL CHAINS (MULTIPLE INDEPENDENT TRACE IDS)
# ═══════════════════════════════════════════════════════════════════════════════
PARALLEL_INPUTS = [
    {
        "trace_id": f"parallel-trace-{i:03d}",
        "execution_id": f"parallel-exec-{i:03d}",
        "tasks": [
            {"task_id": "P1", "depends_on": []},
            {"task_id": "P2", "depends_on": ["P1"]},
        ],
        "constraint_results": [
            {"task_id": "P1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "P2", "is_valid": False, "unsatisfied_dependencies": ["P1"]},
        ],
        "propagation_results": [
            {"task_id": "P1", "affected_tasks": ["P2"], "impact_score": 6},
        ],
    }
    for i in range(1, 6)
]


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

proof_lines: list[str] = []
assertions_passed = 0
assertions_failed = 0


def log(msg: str) -> None:
    proof_lines.append(msg)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


def assert_proof(condition: bool, description: str) -> None:
    global assertions_passed, assertions_failed
    if condition:
        assertions_passed += 1
        log(f"  ✅ PASS — {description}")
    else:
        assertions_failed += 1
        log(f"  ❌ FAIL — {description}")


timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
log(f"# TANTRA Wiring Proof")
log(f"**Generated:** {timestamp}")
log(f"**Chain:** SETU/Input → KESHAV → RAJYA → Sarathi → Core → Bucket → InsightFlow")
log("")

# ─── Scenario 1: Valid End-to-End Chain ───────────────────────────────────────
log(_separator("Scenario 1: Valid End-to-End Chain Execution"))
log("")
log("### Input Contract")
log(_json_block(VALID_INPUT))

result1 = run_tantra_pipeline(VALID_INPUT)

log("")
log("### Full Pipeline Result")
log(_json_block(result1))

# 1.1 Flow completes
assert_proof(result1["status"] == "OK", "Pipeline completed with status=OK")

# 1.2 Contract compatibility — each layer output is a dict
assert_proof(isinstance(result1["keshav_output"], dict), "KESHAV output is a dict (contract compatible)")
assert_proof(isinstance(result1["rajya_output"], dict), "RAJYA output is a dict (contract compatible)")
assert_proof(isinstance(result1["sarathi_output"], dict), "Sarathi output is a dict (contract compatible)")
assert_proof(isinstance(result1["core_output"], dict), "Core output is a dict (contract compatible)")

# 1.3 Trace preservation — byte-identical across all layers
trace_id = VALID_INPUT["trace_id"]
assert_proof(result1["trace_id"] == trace_id, f"Pipeline-level trace_id={trace_id}")
assert_proof(result1["keshav_output"]["trace_id"] == trace_id, f"KESHAV trace_id={trace_id}")
assert_proof(result1["rajya_output"]["trace_id"] == trace_id, f"RAJYA trace_id={trace_id}")
assert_proof(result1["sarathi_output"]["trace_id"] == trace_id, f"Sarathi trace_id={trace_id}")
assert_proof(result1["core_output"]["trace_id"] == trace_id, f"Core trace_id={trace_id}")

# 1.4 Enforcement propagation
assert_proof(
    result1["sarathi_output"]["enforced"] is True,
    "Sarathi enforced=True"
)
assert_proof(
    result1["sarathi_output"]["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1",
    f"Sarathi resolution_signal={result1['sarathi_output']['resolution_signal']}"
)
assert_proof(
    result1["core_output"]["executed"] is True,
    "Core executed=True"
)
assert_proof(
    result1["core_output"]["action"] == "ENFORCE:UNBLOCK_DEPENDENCY:T1",
    f"Core action={result1['core_output']['action']}"
)

# 1.5 Bucket persistence
bucket_record = bucket.read(trace_id)
assert_proof(bucket_record is not None, f"Bucket contains record for trace_id={trace_id}")
assert_proof(
    bucket_record["trace_id"] == trace_id,
    "Bucket record trace_id matches"
)
assert_proof(
    bucket_record["keshav_output"]["root_cause"] == "T1",
    "Bucket preserved KESHAV root_cause=T1"
)
assert_proof(
    bucket_record["core_output"]["executed"] is True,
    "Bucket preserved Core executed=True"
)

log("")
log("### Bucket Record")
log(_json_block(bucket_record))

# 1.6 Observability emission
events = insightflow.get_events()
exec_events = [e for e in events if e["type"] == "EXECUTION" and e["trace_id"] == trace_id]
assert_proof(len(exec_events) == 1, f"InsightFlow emitted exactly 1 EXECUTION event for trace_id={trace_id}")
assert_proof(
    exec_events[0]["root_cause"] == "T1",
    "InsightFlow event root_cause=T1"
)
assert_proof(
    exec_events[0]["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1",
    "InsightFlow event resolution_signal=UNBLOCK_DEPENDENCY:T1"
)

log("")
log("### InsightFlow Observability Event")
log(_json_block(exec_events[0]))


# ─── Scenario 2: Fail-Closed Corruption ──────────────────────────────────────
log(_separator("Scenario 2: Fail-Closed Corruption (Missing trace_id)"))
log("")
log("### Input Contract (Corrupted)")
log(_json_block(CORRUPTED_INPUT))

bucket_before = len(bucket.all_trace_ids())
result2 = run_tantra_pipeline(CORRUPTED_INPUT)

log("")
log("### Full Pipeline Result")
log(_json_block(result2))

assert_proof(result2["status"] == "FAIL", "Pipeline returned FAIL for corrupted input")
assert_proof(result2["keshav_output"]["status"] == "FAIL", "KESHAV returned FAIL")
assert_proof(result2["keshav_output"]["reason"] == "INVALID_INPUT_CONTRACT", "Reason=INVALID_INPUT_CONTRACT")
assert_proof(result2["rajya_output"] is None, "RAJYA never invoked (None)")
assert_proof(result2["sarathi_output"] is None, "Sarathi never invoked (None)")
assert_proof(result2["core_output"] is None, "Core never invoked (None)")

bucket_after = len(bucket.all_trace_ids())
assert_proof(bucket_after == bucket_before, f"Bucket unchanged (before={bucket_before}, after={bucket_after})")

fail_events = insightflow.get_failures()
assert_proof(len(fail_events) >= 1, f"InsightFlow recorded {len(fail_events)} FAILURE event(s)")
assert_proof(
    fail_events[-1]["reason"] == "INVALID_INPUT_CONTRACT",
    "InsightFlow failure reason=INVALID_INPUT_CONTRACT"
)

log("")
log("### InsightFlow Failure Event")
log(_json_block(fail_events[-1]))


# ─── Scenario 3: Clean Graph (No Blocked Tasks) ──────────────────────────────
log(_separator("Scenario 3: Clean Graph — No Blocked Tasks"))
log("")
log("### Input Contract (All tasks valid)")
log(_json_block(CLEAN_INPUT))

result3 = run_tantra_pipeline(CLEAN_INPUT)

log("")
log("### Full Pipeline Result")
log(_json_block(result3))

assert_proof(result3["status"] == "OK", "Pipeline completed OK for clean graph")
clean_trace = CLEAN_INPUT["trace_id"]
assert_proof(result3["trace_id"] == clean_trace, f"trace_id preserved={clean_trace}")
assert_proof(result3["sarathi_output"]["action"] == "NO_ACTION", "Sarathi action=NO_ACTION (no resolution needed)")
assert_proof(result3["core_output"]["executed"] is True, "Core executed=True (no-op pass-through)")

clean_bucket = bucket.read(clean_trace)
assert_proof(clean_bucket is not None, f"Bucket persisted clean run trace_id={clean_trace}")


# ─── Scenario 4: Replay Determinism ──────────────────────────────────────────
log(_separator("Scenario 4: Replay Determinism (3 identical runs)"))
log("")

replay_results = []
for i in range(3):
    bucket.clear()
    insightflow.clear()
    r = run_tantra_pipeline(REPLAY_INPUT)
    # Strip timestamp for comparison (it varies by run)
    keshav_no_ts = {k: v for k, v in r["keshav_output"].items() if k != "timestamp"}
    replay_results.append({
        "keshav_output_no_ts": keshav_no_ts,
        "rajya_output": r["rajya_output"],
        "sarathi_output": r["sarathi_output"],
        "core_output": r["core_output"],
        "status": r["status"],
        "trace_id": r["trace_id"],
    })

assert_proof(
    replay_results[0] == replay_results[1] == replay_results[2],
    "All 3 replays produce byte-identical output (excluding timestamp)"
)

log("")
log("### Replay Run 1 (representative)")
log(_json_block(replay_results[0]))


# ─── Scenario 5: Parallel Independent Chains ─────────────────────────────────
log(_separator("Scenario 5: Parallel Independent Chains (5 distinct trace_ids)"))
log("")

bucket.clear()
insightflow.clear()

parallel_results = []
for inp in PARALLEL_INPUTS:
    r = run_tantra_pipeline(inp)
    parallel_results.append(r)
    log(f"- **{inp['trace_id']}**: status={r['status']}, root_cause={r['keshav_output'].get('root_cause')}")

all_ok = all(r["status"] == "OK" for r in parallel_results)
assert_proof(all_ok, "All 5 parallel chains completed with status=OK")

stored_traces = set(bucket.all_trace_ids())
expected_traces = {inp["trace_id"] for inp in PARALLEL_INPUTS}
assert_proof(stored_traces == expected_traces, f"Bucket contains exactly 5 trace_ids: {sorted(stored_traces)}")

parallel_events = insightflow.get_events()
exec_event_traces = {e["trace_id"] for e in parallel_events if e["type"] == "EXECUTION"}
assert_proof(exec_event_traces == expected_traces, f"InsightFlow emitted EXECUTION events for all 5 traces")

# No cross-contamination
for i, r in enumerate(parallel_results):
    expected_trace = PARALLEL_INPUTS[i]["trace_id"]
    assert_proof(
        r["trace_id"] == expected_trace
        and r["keshav_output"]["trace_id"] == expected_trace
        and r["sarathi_output"]["trace_id"] == expected_trace
        and r["core_output"]["trace_id"] == expected_trace,
        f"Chain {i+1} trace_id isolation: {expected_trace} preserved across all layers"
    )


# ─── Scenario 6: Dependency Chain Validation ─────────────────────────────────
log(_separator("Scenario 6: Layer-by-Layer Dependency Contract Validation"))
log("")
log("Validates each layer individually accepts the exact output of its upstream layer.")
log("")

from analyzer.analyze_blockage import analyze_and_recommend

keshav_out = analyze_and_recommend(VALID_INPUT)
log("### KESHAV Output (analyzer → RAJYA input)")
log(_json_block(keshav_out))
assert_proof("trace_id" in keshav_out, "KESHAV output contains trace_id")
assert_proof("resolution_signal" in keshav_out, "KESHAV output contains resolution_signal")

rajya_out = rajya.consume(keshav_out, VALID_INPUT["trace_id"])
log("")
log("### RAJYA Output (rajya → Sarathi input)")
log(_json_block(rajya_out))
assert_proof(rajya_out["trace_id"] == VALID_INPUT["trace_id"], "RAJYA preserved trace_id")
assert_proof(rajya_out is keshav_out, "RAJYA performs zero-transformation (same object reference)")

sarathi_out = sarathi.enforce(rajya_out)
log("")
log("### Sarathi Output (sarathi → Core input)")
log(_json_block(sarathi_out))
assert_proof(sarathi_out["trace_id"] == VALID_INPUT["trace_id"], "Sarathi preserved trace_id")
assert_proof(sarathi_out["enforced"] is True, "Sarathi enforced=True")

core_out = core.execute(sarathi_out)
log("")
log("### Core Output (core → Bucket input)")
log(_json_block(core_out))
assert_proof(core_out["trace_id"] == VALID_INPUT["trace_id"], "Core preserved trace_id")
assert_proof(core_out["executed"] is True, "Core executed=True")

# Bucket write
bucket.clear()
bucket.write(core_out, keshav_out)
record = bucket.read(VALID_INPUT["trace_id"])
log("")
log("### Bucket Record (persisted truth)")
log(_json_block(record))
assert_proof(record is not None, "Bucket persisted the record")
assert_proof(record["trace_id"] == VALID_INPUT["trace_id"], "Bucket record trace_id matches")


# ═══════════════════════════════════════════════════════════════════════════════
# FINAL VERDICT
# ═══════════════════════════════════════════════════════════════════════════════
log("")
log("━" * 80)
log("## FINAL VERDICT")
log("━" * 80)
log("")
log(f"**Total Assertions:** {assertions_passed + assertions_failed}")
log(f"**Passed:** {assertions_passed}")
log(f"**Failed:** {assertions_failed}")
log("")

if assertions_failed == 0:
    log("### ✅ ALL ASSERTIONS PASSED")
    log("")
    log("KESHAV is a **fully wired, replay-safe, production-ready ecosystem participant**")
    log("in the live TANTRA execution chain.")
    log("")
    log("**Proven:**")
    log("- Complete chain executes without manual intervention")
    log("- Contract compatibility verified across all 6 layers")
    log("- trace_id preserved byte-identical through entire chain")
    log("- Enforcement propagation verified (Sarathi → Core)")
    log("- Bucket persistence verified (write on success, no write on failure)")
    log("- Observability emission verified (InsightFlow EXECUTION + FAILURE events)")
    log("- Replay determinism verified (3 identical runs)")
    log("- Parallel chain isolation verified (5 independent trace_ids)")
    log("- Layer-by-layer dependency contract validation complete")
else:
    log(f"### ❌ {assertions_failed} ASSERTION(S) FAILED")
    log("TANTRA wiring is NOT proven. Review failures above.")

# Write to file
with open("TANTRA_WIRING_PROOF.md", "w", encoding="utf-8") as f:
    f.write("\n".join(proof_lines) + "\n")

print(f"\n{'=' * 40}")
print(f"Proof written to TANTRA_WIRING_PROOF.md")
print(f"Assertions: {assertions_passed} passed, {assertions_failed} failed")
print(f"{'=' * 40}")

sys.exit(0 if assertions_failed == 0 else 1)
