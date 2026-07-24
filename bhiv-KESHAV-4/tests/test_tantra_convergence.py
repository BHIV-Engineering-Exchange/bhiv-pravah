"""
TANTRA Convergence Tests — Final Execution Lock

Covers all 6 phases:
  Phase 1 — RAJYA Integration (5 parallel traces)
  Phase 2 — InsightFlow Observability (read-only, structured events)
  Phase 3 — Full TANTRA Chain (SETU → KESHAV → RAJYA → Sarathi → Core → Bucket)
  Phase 4 — Trace Continuity (trace_id identical across all layers)
  Phase 5 — Deterministic Replay (10 runs, byte-for-byte identical)
  Phase 6 — Failure + Truth Verification (3 failure cases, Bucket integrity)
"""

import concurrent.futures
import copy
import json

import pytest

from tantra import bucket, insightflow
from tantra.pipeline import run_tantra_pipeline

# ── fixtures ──────────────────────────────────────────────────────────────────

VALID_INPUT = {
    "trace_id": "tantra-trace-001",
    "execution_id": "exec-tantra-001",
    "tasks": [
        {"task_id": "T1", "depends_on": []},
        {"task_id": "T2", "depends_on": ["T1"]},
        {"task_id": "T3", "depends_on": ["T2"]},
    ],
    "constraint_results": [
        {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
        {"task_id": "T3", "is_valid": True,  "unsatisfied_dependencies": []},
    ],
    "propagation_results": [
        {"task_id": "T1", "affected_tasks": ["T2", "T3"], "impact_score": 10},
        {"task_id": "T2", "affected_tasks": ["T3"],       "impact_score": 4},
    ],
}

PARALLEL_INPUTS = [
    {
        "trace_id": f"parallel-trace-{i:03d}",
        "execution_id": f"exec-parallel-{i:03d}",
        "tasks": [{"task_id": "T1", "depends_on": []}],
        "constraint_results": [{"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []}],
        "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": i}],
    }
    for i in range(1, 6)
]


@pytest.fixture(autouse=True)
def reset_stores():
    """Isolate each test — clear Bucket and InsightFlow before every test."""
    bucket.clear()
    insightflow.clear()
    yield
    bucket.clear()
    insightflow.clear()


# ── Phase 1: RAJYA Integration ────────────────────────────────────────────────

def test_rajya_consumes_keshav_output_without_failure():
    """RAJYA must accept KESHAV output directly — no schema transformation."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "OK"
    assert result["rajya_output"] is result["keshav_output"], (  # identity check: zero-transformation proof
        "RAJYA must return the same object — zero transformation"
    )


def test_rajya_five_parallel_traces():
    """Run 5 concurrent flows through RAJYA. All must succeed."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [
            pool.submit(run_tantra_pipeline, copy.deepcopy(inp))
            for inp in PARALLEL_INPUTS
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r["status"] == "OK" for r in results), (
        f"Some parallel traces failed: {[r for r in results if r['status'] != 'OK']}"
    )
    trace_ids = {r["trace_id"] for r in results}
    assert len(trace_ids) == 5, "All 5 parallel traces must have distinct trace_ids"


# ── Phase 2: InsightFlow Observability ────────────────────────────────────────

def test_insightflow_emits_structured_event():
    """InsightFlow must emit root_cause, impact_score, severity, resolution_signal, trace_id."""
    run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    events = insightflow.get_events()
    assert len(events) == 1
    event = events[0]
    assert event["type"] == "EXECUTION"
    for field in ("trace_id", "root_cause", "impact_score", "severity", "resolution_signal"):
        assert field in event, f"InsightFlow event missing field: {field}"


def test_insightflow_does_not_mutate_keshav_output():
    """InsightFlow is read-only — must not modify KESHAV output."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    keshav = result["keshav_output"]
    snapshot_before = json.dumps(keshav, sort_keys=True)
    insightflow.emit(keshav)  # emit again — must not change anything
    snapshot_after = json.dumps(keshav, sort_keys=True)
    assert snapshot_before == snapshot_after


def test_insightflow_shows_failure_event():
    """Failure inputs must appear as FAILURE events in InsightFlow."""
    run_tantra_pipeline({"execution_id": "exec-x"})  # missing trace_id
    failures = insightflow.get_failures()
    assert len(failures) == 1
    assert failures[0]["type"] == "FAILURE"


# ── Phase 3: Full TANTRA Chain ────────────────────────────────────────────────

def test_full_tantra_chain_all_layers_active():
    """All layers must be active — no None outputs on success."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "OK"
    for layer in ("keshav_output", "rajya_output", "sarathi_output", "core_output"):
        assert result[layer] is not None, f"Layer {layer} must not be None"


def test_full_chain_keshav_output_contract():
    """KESHAV output must have all 7 TANTRA contract keys."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert set(result["keshav_output"].keys()) == {
        "trace_id", "execution_id", "root_cause", "resolution_signal",
        "impact_score", "severity", "timestamp",
    }


def test_full_chain_sarathi_consumes_resolution_signal():
    """Sarathi must receive and act on resolution_signal from RAJYA."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    sarathi = result["sarathi_output"]
    assert sarathi["enforced"] is True
    assert sarathi["resolution_signal"] == result["keshav_output"]["resolution_signal"]


def test_full_chain_core_executes_action():
    """Core must execute the action from Sarathi."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    core_out = result["core_output"]
    assert core_out["executed"] is True
    assert core_out["action"] == result["sarathi_output"]["action"]


# ── Phase 4: Trace Continuity ─────────────────────────────────────────────────

def test_trace_id_identical_across_all_layers():
    """trace_id must be identical in KESHAV, RAJYA, Sarathi, Core, and Bucket."""
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    expected = VALID_INPUT["trace_id"]

    assert result["keshav_output"]["trace_id"] == expected,  "KESHAV trace_id mismatch"
    assert result["rajya_output"]["trace_id"] == expected,   "RAJYA trace_id mismatch"
    assert result["sarathi_output"]["trace_id"] == expected, "Sarathi trace_id mismatch"
    assert result["core_output"]["trace_id"] == expected,    "Core trace_id mismatch"

    stored = bucket.read(expected)
    assert stored is not None, "Bucket must have stored the trace"
    assert stored["trace_id"] == expected, "Bucket trace_id mismatch"


def test_trace_id_in_insightflow_event():
    """InsightFlow event must carry the same trace_id."""
    run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    event = insightflow.get_events()[0]
    assert event["trace_id"] == VALID_INPUT["trace_id"]


# ── Phase 5: Deterministic Replay ─────────────────────────────────────────────

def _serialize_result(result: dict) -> str:
    """Canonical JSON of pipeline result — exclude timestamp."""
    stable = {
        k: (
            {kk: vv for kk, vv in v.items() if kk != "timestamp"}
            if isinstance(v, dict) else v
        )
        for k, v in result.items()
        if k not in ("error",)
    }
    return json.dumps(stable, sort_keys=True, separators=(",", ":"))


def test_deterministic_replay_10_runs():
    """Same input must produce byte-for-byte identical output across 10 runs."""
    outputs = [
        _serialize_result(run_tantra_pipeline(copy.deepcopy(VALID_INPUT)))
        for _ in range(10)
    ]
    for i, out in enumerate(outputs[1:], start=2):
        assert out == outputs[0], (
            f"Run {i} differs from run 1\n"
            f"  run 1: {outputs[0][:120]}\n"
            f"  run {i}: {out[:120]}"
        )


def test_deterministic_replay_bucket_identical():
    """Bucket must store identical truth across 10 replays of the same trace."""
    stored_snapshots = []
    for _ in range(10):
        bucket.clear()
        run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
        stored = bucket.read(VALID_INPUT["trace_id"])
        assert stored is not None
        snap = json.dumps(
            {k: v for k, v in stored["keshav_output"].items() if k != "timestamp"},
            sort_keys=True,
        )
        stored_snapshots.append(snap)

    for i, snap in enumerate(stored_snapshots[1:], start=2):
        assert snap == stored_snapshots[0], f"Bucket truth differs on replay {i}"


# ── Phase 6: Failure + Truth Verification ─────────────────────────────────────

def test_failure_missing_trace_id_fail_closed():
    """Missing trace_id → FAIL, no Bucket write."""
    result = run_tantra_pipeline({"execution_id": "exec-no-trace"})
    assert result["status"] == "FAIL"
    assert result["rajya_output"] is None
    assert result["sarathi_output"] is None
    assert result["core_output"] is None
    assert len(bucket.all_trace_ids()) == 0


def test_failure_invalid_schema_fail_closed():
    """Non-dict input (invalid schema) → FAIL, no Bucket write."""
    result = run_tantra_pipeline("not-a-dict")
    assert result["status"] == "FAIL"
    assert len(bucket.all_trace_ids()) == 0


def test_failure_corrupted_propagation_no_bucket_write():
    """
    Corrupted propagation input (trace_id missing) → FAIL, no Bucket write.
    Simulates a corrupted upstream payload.
    """
    corrupted = {
        "execution_id": "exec-corrupted",
        # trace_id intentionally omitted
        "tasks": [{"task_id": "T1", "depends_on": []}],
        "constraint_results": [{"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []}],
        "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 5}],
    }
    result = run_tantra_pipeline(corrupted)
    assert result["status"] == "FAIL"
    assert len(bucket.all_trace_ids()) == 0


def test_failures_visible_in_insightflow():
    """All 3 failure cases must appear as FAILURE events in InsightFlow."""
    run_tantra_pipeline({"execution_id": "exec-no-trace"})
    run_tantra_pipeline("not-a-dict")
    run_tantra_pipeline({"execution_id": "exec-corrupted"})

    failures = insightflow.get_failures()
    assert len(failures) == 3, f"Expected 3 failure events, got {len(failures)}"


def test_no_partial_execution_on_failure():
    """On failure, downstream layers (Sarathi, Core) must not execute."""
    result = run_tantra_pipeline({"execution_id": "exec-partial"})
    assert result["sarathi_output"] is None
    assert result["core_output"] is None


def test_successful_run_stored_in_bucket():
    """Successful run must be stored in Bucket and be retrievable."""
    run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    stored = bucket.read(VALID_INPUT["trace_id"])
    assert stored is not None
    assert stored["trace_id"] == VALID_INPUT["trace_id"]
    assert "keshav_output" in stored
    assert "core_output" in stored


def test_bucket_truth_reconstructable():
    """Stored Bucket truth must contain enough data to reconstruct the execution."""
    run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    stored = bucket.read(VALID_INPUT["trace_id"])
    keshav = stored["keshav_output"]
    assert keshav["root_cause"] == "T1"
    assert keshav["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1"
    assert keshav["impact_score"] == 10
    assert keshav["severity"] == "HIGH"


def test_failed_runs_not_in_bucket():
    """Failed runs must never write to Bucket."""
    run_tantra_pipeline({"execution_id": "exec-fail-1"})
    run_tantra_pipeline("bad")
    assert len(bucket.all_trace_ids()) == 0


# ── Pipeline layer failure catch blocks (L46-47, L52-53, L58-59) ──────────────

def test_pipeline_sarathi_failure_is_fail_closed(monkeypatch):
    """Sarathi raising ValueError → pipeline FAIL, no Bucket write (L52-53)."""
    from tantra import sarathi
    monkeypatch.setattr(sarathi, "enforce", lambda _: (_ for _ in ()).throw(ValueError("Sarathi: missing trace_id")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert result["sarathi_output"] is None
    assert result["core_output"] is None
    assert len(bucket.all_trace_ids()) == 0


def test_pipeline_core_failure_is_fail_closed(monkeypatch):
    """Core raising ValueError → pipeline FAIL, no Bucket write (L58-59)."""
    from tantra import core
    monkeypatch.setattr(core, "execute", lambda _: (_ for _ in ()).throw(ValueError("Core: missing trace_id")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert result["core_output"] is None
    assert len(bucket.all_trace_ids()) == 0


def test_pipeline_rajya_trace_mismatch_is_fail_closed(monkeypatch):
    """RAJYA raising ValueError on trace_id mismatch → pipeline FAIL (L46-47)."""
    from tantra import rajya
    monkeypatch.setattr(rajya, "consume", lambda _o, _t: (_ for _ in ()).throw(ValueError("RAJYA: trace_id mismatch")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert result["rajya_output"] is None
    assert len(bucket.all_trace_ids()) == 0
