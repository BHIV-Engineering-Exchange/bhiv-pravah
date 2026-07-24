"""
PHASE 4 — REPLAY & DETERMINISM VALIDATION

Proves replay-safe operation through:
  1. Execute identical inputs multiple times (10 runs)
  2. Compare outputs (field-by-field)
  3. Compare hashes (SHA-256 of serialized output)
  4. Compare trace artifacts (trace_id, root_cause, resolution_signal)
  5. Compare bucket persistence records (identical across replays)
  6. Verify deterministic replay behavior (hash equality proof)

Output: REPLAY_DETERMINISM_PROOF.md
"""

import hashlib
import json
import sys
from datetime import datetime, timezone

from tantra import bucket, insightflow
from tantra.pipeline import run_tantra_pipeline


def safe_print(msg: str) -> None:
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


# ═══════════════════════════════════════════════════════════════════════════════
# TEST INPUTS
# ═══════════════════════════════════════════════════════════════════════════════

# Input A: complex blocked graph
INPUT_A = {
    "trace_id": "replay-trace-A",
    "execution_id": "replay-exec-A",
    "tasks": [
        {"task_id": "T1", "depends_on": []},
        {"task_id": "T2", "depends_on": ["T1"]},
        {"task_id": "T3", "depends_on": ["T1"]},
        {"task_id": "T4", "depends_on": ["T2", "T3"]},
        {"task_id": "T5", "depends_on": ["T4"]},
    ],
    "constraint_results": [
        {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
        {"task_id": "T3", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
        {"task_id": "T4", "is_valid": False, "unsatisfied_dependencies": ["T2", "T3"]},
        {"task_id": "T5", "is_valid": False, "unsatisfied_dependencies": ["T4"]},
    ],
    "propagation_results": [
        {"task_id": "T1", "affected_tasks": ["T2", "T3", "T4", "T5"], "impact_score": 20},
        {"task_id": "T2", "affected_tasks": ["T4", "T5"], "impact_score": 8},
        {"task_id": "T3", "affected_tasks": ["T4", "T5"], "impact_score": 8},
    ],
}

# Input B: clean graph (no blocked tasks)
INPUT_B = {
    "trace_id": "replay-trace-B",
    "execution_id": "replay-exec-B",
    "tasks": [
        {"task_id": "X1", "depends_on": []},
        {"task_id": "X2", "depends_on": ["X1"]},
    ],
    "constraint_results": [
        {"task_id": "X1", "is_valid": True, "unsatisfied_dependencies": []},
        {"task_id": "X2", "is_valid": True, "unsatisfied_dependencies": []},
    ],
    "propagation_results": [],
}

# Input C: corrupted (fail-closed)
INPUT_C = {
    "execution_id": "corrupt-001",
    "tasks": "not-a-list",
}

NUM_REPLAYS = 10

proof_lines: list[str] = []
assertions_passed = 0
assertions_failed = 0


def log(msg: str) -> None:
    proof_lines.append(msg)
    safe_print(msg)


def assert_proof(condition: bool, desc: str) -> None:
    global assertions_passed, assertions_failed
    if condition:
        assertions_passed += 1
        log(f"  PASS -- {desc}")
    else:
        assertions_failed += 1
        log(f"  FAIL -- {desc}")


def _json_block(data) -> str:
    return f"```json\n{json.dumps(data, indent=2, sort_keys=True)}\n```"


def _strip_timestamp(output: dict) -> dict:
    """Remove timestamp from KESHAV output for deterministic comparison."""
    result = dict(output)
    ko = dict(result.get("keshav_output", {}))
    ko.pop("timestamp", None)
    result["keshav_output"] = ko
    # RAJYA output is the same object reference, so also strip
    ro = result.get("rajya_output")
    if isinstance(ro, dict):
        ro = dict(ro)
        ro.pop("timestamp", None)
        result["rajya_output"] = ro
    return result


def _hash_output(output: dict) -> str:
    """SHA-256 of deterministic JSON serialization."""
    canonical = json.dumps(output, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
log("# KESHAV Replay & Determinism Proof")
log(f"**Generated:** {timestamp}")
log(f"**Replay Count:** {NUM_REPLAYS} runs per input")
log("")

# ─── Test 1: Blocked Graph Replay ────────────────────────────────────────────
log("---")
log("## Test 1: Blocked Graph Replay (Input A)")
log("")
log("### Input")
log(_json_block(INPUT_A))
log("")

results_a: list[dict] = []
hashes_a: list[str] = []
bucket_records_a: list[dict] = []

for i in range(NUM_REPLAYS):
    bucket.clear()
    insightflow.clear()
    r = run_tantra_pipeline(INPUT_A)
    stripped = _strip_timestamp(r)
    h = _hash_output(stripped)
    results_a.append(stripped)
    hashes_a.append(h)
    br = bucket.read("replay-trace-A")
    # Also strip timestamp from bucket record's keshav_output
    if br:
        br_copy = dict(br)
        ko_copy = dict(br_copy.get("keshav_output", {}))
        ko_copy.pop("timestamp", None)
        br_copy["keshav_output"] = ko_copy
        bucket_records_a.append(br_copy)

log("### Output Comparison")
log("")
log("| Run | SHA-256 Hash | Status | Root Cause | Resolution Signal |")
log("|-----|-------------|--------|------------|-------------------|")
for i, (r, h) in enumerate(zip(results_a, hashes_a)):
    ko = r["keshav_output"]
    log(f"| {i+1:2d}  | `{h[:16]}...` | {r['status']} | {ko.get('root_cause')} | {ko.get('resolution_signal')} |")
log("")

# 1.1 All outputs identical
all_outputs_equal = all(r == results_a[0] for r in results_a[1:])
assert_proof(all_outputs_equal, f"All {NUM_REPLAYS} outputs are field-by-field identical")

# 1.2 All hashes identical
all_hashes_equal = len(set(hashes_a)) == 1
assert_proof(all_hashes_equal, f"All {NUM_REPLAYS} SHA-256 hashes are identical: {hashes_a[0][:32]}...")

# 1.3 Trace artifacts preserved
for i, r in enumerate(results_a):
    ko = r["keshav_output"]
    assert_proof(
        ko["trace_id"] == "replay-trace-A"
        and r["sarathi_output"]["trace_id"] == "replay-trace-A"
        and r["core_output"]["trace_id"] == "replay-trace-A",
        f"Run {i+1}: trace_id='replay-trace-A' preserved across all layers"
    )

# 1.4 Bucket records identical
all_bucket_equal = all(br == bucket_records_a[0] for br in bucket_records_a[1:])
assert_proof(all_bucket_equal, f"All {NUM_REPLAYS} bucket persistence records are identical")

log("")
log("### Representative Output (Run 1)")
log(_json_block(results_a[0]))
log("")
log("### Representative Bucket Record (Run 1)")
log(_json_block(bucket_records_a[0]))

# ─── Test 2: Clean Graph Replay ──────────────────────────────────────────────
log("")
log("---")
log("## Test 2: Clean Graph Replay (Input B)")
log("")
log("### Input")
log(_json_block(INPUT_B))
log("")

results_b: list[dict] = []
hashes_b: list[str] = []

for i in range(NUM_REPLAYS):
    bucket.clear()
    insightflow.clear()
    r = run_tantra_pipeline(INPUT_B)
    stripped = _strip_timestamp(r)
    h = _hash_output(stripped)
    results_b.append(stripped)
    hashes_b.append(h)

log("### Output Comparison")
log("")
log("| Run | SHA-256 Hash | Status | Root Cause | Sarathi Action |")
log("|-----|-------------|--------|------------|----------------|")
for i, (r, h) in enumerate(zip(results_b, hashes_b)):
    ko = r["keshav_output"]
    log(f"| {i+1:2d}  | `{h[:16]}...` | {r['status']} | {ko.get('root_cause')} | {r['sarathi_output']['action']} |")
log("")

all_b_equal = all(r == results_b[0] for r in results_b[1:])
assert_proof(all_b_equal, f"All {NUM_REPLAYS} clean graph outputs are field-by-field identical")

all_b_hashes_equal = len(set(hashes_b)) == 1
assert_proof(all_b_hashes_equal, f"All {NUM_REPLAYS} clean graph SHA-256 hashes are identical: {hashes_b[0][:32]}...")

# ─── Test 3: Fail-Closed Replay ──────────────────────────────────────────────
log("")
log("---")
log("## Test 3: Fail-Closed Replay (Input C -- corrupted)")
log("")
log("### Input")
log(_json_block(INPUT_C))
log("")

results_c: list[dict] = []
hashes_c: list[str] = []

for i in range(NUM_REPLAYS):
    bucket.clear()
    insightflow.clear()
    r = run_tantra_pipeline(INPUT_C)
    # No timestamp stripping needed for FAIL outputs
    h = _hash_output(r)
    results_c.append(r)
    hashes_c.append(h)
    # Verify bucket stays empty
    assert_proof(len(bucket.all_trace_ids()) == 0, f"Run {i+1}: Bucket empty after corrupted input")

log("### Output Comparison")
log("")
log("| Run | SHA-256 Hash | Status | Reason |")
log("|-----|-------------|--------|--------|")
for i, (r, h) in enumerate(zip(results_c, hashes_c)):
    ko = r["keshav_output"]
    log(f"| {i+1:2d}  | `{h[:16]}...` | {r['status']} | {ko.get('reason')} |")
log("")

all_c_equal = all(r == results_c[0] for r in results_c[1:])
assert_proof(all_c_equal, f"All {NUM_REPLAYS} fail-closed outputs are field-by-field identical")

all_c_hashes_equal = len(set(hashes_c)) == 1
assert_proof(all_c_hashes_equal, f"All {NUM_REPLAYS} fail-closed SHA-256 hashes are identical: {hashes_c[0][:32]}...")

# ─── Test 4: Cross-Input Hash Isolation ───────────────────────────────────────
log("")
log("---")
log("## Test 4: Cross-Input Hash Isolation")
log("")

assert_proof(hashes_a[0] != hashes_b[0], f"Input A hash != Input B hash (different inputs produce different outputs)")
assert_proof(hashes_a[0] != hashes_c[0], f"Input A hash != Input C hash (valid vs corrupted)")
assert_proof(hashes_b[0] != hashes_c[0], f"Input B hash != Input C hash (clean vs corrupted)")

# ─── Test 5: InsightFlow Event Determinism ────────────────────────────────────
log("")
log("---")
log("## Test 5: InsightFlow Event Determinism")
log("")

insightflow.clear()
for _ in range(3):
    bucket.clear()
    run_tantra_pipeline(INPUT_A)

events = insightflow.get_events()
exec_events = [e for e in events if e["type"] == "EXECUTION"]
assert_proof(len(exec_events) == 3, f"InsightFlow recorded exactly 3 EXECUTION events across 3 replays")

# All events should have same trace_id, root_cause, severity, resolution_signal
for i, ev in enumerate(exec_events):
    assert_proof(
        ev["trace_id"] == "replay-trace-A"
        and ev["root_cause"] == "T1"
        and ev["severity"] == "HIGH"
        and ev["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1",
        f"InsightFlow event {i+1}: trace_id, root_cause, severity, resolution_signal all match"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# FINAL VERDICT
# ═══════════════════════════════════════════════════════════════════════════════
log("")
log("---")
log("## FINAL VERDICT")
log("")
log(f"**Total Assertions:** {assertions_passed + assertions_failed}")
log(f"**Passed:** {assertions_passed}")
log(f"**Failed:** {assertions_failed}")
log("")

if assertions_failed == 0:
    log("### ALL ASSERTIONS PASSED")
    log("")
    log("KESHAV replay-safe operation is **fully proven**.")
    log("")
    log("**Proven:**")
    log(f"- {NUM_REPLAYS} identical runs per input produce byte-identical outputs")
    log(f"- SHA-256 hash equality verified across all {NUM_REPLAYS} runs for 3 input classes")
    log("- Trace artifacts (trace_id, root_cause, resolution_signal) are identical across replays")
    log("- Bucket persistence records are identical across replays")
    log("- Fail-closed replays produce identical FAIL outputs with zero Bucket writes")
    log("- Cross-input hash isolation verified (different inputs -> different hashes)")
    log("- InsightFlow observability events are deterministic across replays")
else:
    log(f"### {assertions_failed} ASSERTION(S) FAILED")
    log("Replay determinism is NOT proven. Review failures above.")

# Write to file
with open("REPLAY_DETERMINISM_PROOF.md", "w", encoding="utf-8") as f:
    f.write("\n".join(proof_lines) + "\n")

safe_print(f"\n{'=' * 40}")
safe_print(f"Proof written to REPLAY_DETERMINISM_PROOF.md")
safe_print(f"Assertions: {assertions_passed} passed, {assertions_failed} failed")
safe_print(f"{'=' * 40}")

sys.exit(0 if assertions_failed == 0 else 1)
