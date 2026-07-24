"""
Tests for Phase 8 — Determinism Proof

Rules:
- Same input → byte-for-byte identical output every time (excluding timestamp)
- No variation allowed across any number of runs
- Covers all scenario types: normal, edge, complex

Proof method:
- Run analyze_blockage(input) N times
- Serialize each output (excluding timestamp) to JSON with sorted keys
- Assert all N outputs are identical strings
"""

import copy
import json

from analyzer.analyze_blockage import analyze_and_recommend as analyze_blockage

RUNS = 10


# ── helper ────────────────────────────────────────────────────────────────────

def serialize(result: dict) -> str:
    """Canonical JSON string — sorted keys, timestamp excluded."""
    stable = {k: v for k, v in result.items() if k != "timestamp"}
    return json.dumps(stable, sort_keys=True, separators=(",", ":"))

def run_n_times(input_data: dict, n: int = RUNS) -> list[str]:
    return [serialize(analyze_blockage(copy.deepcopy(input_data))) for _ in range(n)]

def assert_all_identical(outputs: list[str], label: str):
    for i, out in enumerate(outputs[1:], start=2):
        assert out == outputs[0], (
            f"{label}: run {i} differs from run 1\n"
            f"  run 1: {outputs[0][:120]}\n"
            f"  run {i}: {out[:120]}"
        )


# ── proof fixtures ────────────────────────────────────────────────────────────

FIXTURES = {

    "normal_mixed": {
        "trace_id": "trace-normal",
        "execution_id": "proof-normal",
        "tasks": [
            {"task_id": "T1", "depends_on": []},
            {"task_id": "T2", "depends_on": ["T1"]},
            {"task_id": "T3", "depends_on": ["T1"]},
            {"task_id": "T4", "depends_on": ["T2", "T3"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
            {"task_id": "T3", "is_valid": True,  "unsatisfied_dependencies": []},
            {"task_id": "T4", "is_valid": False, "unsatisfied_dependencies": ["T2"]},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2", "T4"], "impact_score": 9},
            {"task_id": "T2", "affected_tasks": ["T4"],       "impact_score": 4},
            {"task_id": "T3", "affected_tasks": ["T4"],       "impact_score": 2},
            {"task_id": "T4", "affected_tasks": [],           "impact_score": 0},
        ],
    },

    "no_blocked_tasks": {
        "trace_id": "trace-no-blocked",
        "execution_id": "proof-no-blocked",
        "tasks": [
            {"task_id": "T1", "depends_on": []},
            {"task_id": "T2", "depends_on": ["T1"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": True, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": True, "unsatisfied_dependencies": []},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2"], "impact_score": 5},
            {"task_id": "T2", "affected_tasks": [],     "impact_score": 0},
        ],
    },

    "all_tasks_blocked": {
        "trace_id": "trace-all-blocked",
        "execution_id": "proof-all-blocked",
        "tasks": [
            {"task_id": "T1", "depends_on": []},
            {"task_id": "T2", "depends_on": ["T1"]},
            {"task_id": "T3", "depends_on": ["T2"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
            {"task_id": "T3", "is_valid": False, "unsatisfied_dependencies": ["T2"]},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2", "T3"], "impact_score": 10},
            {"task_id": "T2", "affected_tasks": ["T3"],       "impact_score": 5},
            {"task_id": "T3", "affected_tasks": [],           "impact_score": 0},
        ],
    },

    "deep_chain": {
        "trace_id": "trace-deep",
        "execution_id": "proof-deep-chain",
        "tasks": [
            {"task_id": "T1", "depends_on": []},
            {"task_id": "T2", "depends_on": ["T1"]},
            {"task_id": "T3", "depends_on": ["T2"]},
            {"task_id": "T4", "depends_on": ["T3"]},
            {"task_id": "T5", "depends_on": ["T4"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
            {"task_id": "T3", "is_valid": False, "unsatisfied_dependencies": ["T2"]},
            {"task_id": "T4", "is_valid": False, "unsatisfied_dependencies": ["T3"]},
            {"task_id": "T5", "is_valid": False, "unsatisfied_dependencies": ["T4"]},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2","T3","T4","T5"], "impact_score": 20},
            {"task_id": "T2", "affected_tasks": ["T3","T4","T5"],      "impact_score": 14},
            {"task_id": "T3", "affected_tasks": ["T4","T5"],           "impact_score": 8},
            {"task_id": "T4", "affected_tasks": ["T5"],                "impact_score": 3},
            {"task_id": "T5", "affected_tasks": [],                    "impact_score": 0},
        ],
    },

    "circular_dependency": {
        "trace_id": "trace-circular",
        "execution_id": "proof-circular",
        "tasks": [
            {"task_id": "T1", "depends_on": ["T2"]},
            {"task_id": "T2", "depends_on": ["T1"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": ["T2"]},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2"], "impact_score": 5},
            {"task_id": "T2", "affected_tasks": ["T1"], "impact_score": 5},
        ],
    },

    "self_dependency": {
        "trace_id": "trace-self",
        "execution_id": "proof-self-dep",
        "tasks": [{"task_id": "T1", "depends_on": ["T1"]}],
        "constraint_results": [{"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": ["T1"]}],
        "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 3}],
    },

    "missing_dependency": {
        "trace_id": "trace-missing",
        "execution_id": "proof-missing-dep",
        "tasks": [{"task_id": "T2", "depends_on": ["GHOST"]}],
        "constraint_results": [{"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["GHOST"]}],
        "propagation_results": [{"task_id": "T2", "affected_tasks": [], "impact_score": 6}],
    },

    "disconnected_components": {
        "trace_id": "trace-disconnected",
        "execution_id": "proof-disconnected",
        "tasks": [
            {"task_id": "A1", "depends_on": []},
            {"task_id": "A2", "depends_on": ["A1"]},
            {"task_id": "B1", "depends_on": []},
            {"task_id": "B2", "depends_on": ["B1"]},
        ],
        "constraint_results": [
            {"task_id": "A1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "A2", "is_valid": False, "unsatisfied_dependencies": ["A1"]},
            {"task_id": "B1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "B2", "is_valid": False, "unsatisfied_dependencies": ["B1"]},
        ],
        "propagation_results": [
            {"task_id": "A1", "affected_tasks": ["A2"], "impact_score": 5},
            {"task_id": "A2", "affected_tasks": [],     "impact_score": 1},
            {"task_id": "B1", "affected_tasks": ["B2"], "impact_score": 9},
            {"task_id": "B2", "affected_tasks": [],     "impact_score": 2},
        ],
    },

    "multiple_root_causes": {
        "trace_id": "trace-multi-root",
        "execution_id": "proof-multi-root",
        "tasks": [
            {"task_id": "T1", "depends_on": []},
            {"task_id": "T2", "depends_on": ["T1"]},
            {"task_id": "T3", "depends_on": []},
            {"task_id": "T4", "depends_on": ["T3"]},
        ],
        "constraint_results": [
            {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
            {"task_id": "T3", "is_valid": False, "unsatisfied_dependencies": []},
            {"task_id": "T4", "is_valid": False, "unsatisfied_dependencies": ["T3"]},
        ],
        "propagation_results": [
            {"task_id": "T1", "affected_tasks": ["T2"], "impact_score": 3},
            {"task_id": "T2", "affected_tasks": [],     "impact_score": 1},
            {"task_id": "T3", "affected_tasks": ["T4"], "impact_score": 8},
            {"task_id": "T4", "affected_tasks": [],     "impact_score": 2},
        ],
    },
}


# ── proof tests ───────────────────────────────────────────────────────────────

def test_determinism_normal_mixed():
    assert_all_identical(run_n_times(FIXTURES["normal_mixed"]), "normal_mixed")

def test_determinism_no_blocked_tasks():
    assert_all_identical(run_n_times(FIXTURES["no_blocked_tasks"]), "no_blocked_tasks")

def test_determinism_all_tasks_blocked():
    assert_all_identical(run_n_times(FIXTURES["all_tasks_blocked"]), "all_tasks_blocked")

def test_determinism_deep_chain():
    assert_all_identical(run_n_times(FIXTURES["deep_chain"]), "deep_chain")

def test_determinism_circular_dependency():
    assert_all_identical(run_n_times(FIXTURES["circular_dependency"]), "circular_dependency")

def test_determinism_self_dependency():
    assert_all_identical(run_n_times(FIXTURES["self_dependency"]), "self_dependency")

def test_determinism_missing_dependency():
    assert_all_identical(run_n_times(FIXTURES["missing_dependency"]), "missing_dependency")

def test_determinism_disconnected_components():
    assert_all_identical(run_n_times(FIXTURES["disconnected_components"]), "disconnected_components")

def test_determinism_multiple_root_causes():
    assert_all_identical(run_n_times(FIXTURES["multiple_root_causes"]), "multiple_root_causes")

def test_input_not_mutated():
    """Input dict must be identical before and after analyze_blockage call."""
    input_data = copy.deepcopy(FIXTURES["normal_mixed"])
    snapshot_before = json.dumps(input_data, sort_keys=True)
    analyze_blockage(input_data)
    snapshot_after = json.dumps(input_data, sort_keys=True)
    assert snapshot_before == snapshot_after, "Input was mutated by analyze_blockage"
