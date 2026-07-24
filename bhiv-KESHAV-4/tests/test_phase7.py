"""
Tests for Phase 7 — Edge Case Coverage

All tests run end-to-end through analyze_and_recommend(input).
Input must include trace_id. Output is TANTRA contract:
  trace_id, execution_id, root_cause, resolution_signal, impact_score, severity, timestamp
"""

from analyzer.analyze_blockage import analyze_and_recommend as analyze_blockage

# ── helpers ───────────────────────────────────────────────────────────────────

def make_task(task_id, depends_on=None):
    return {"task_id": task_id, "depends_on": depends_on or []}

def make_constraint(task_id, is_valid, unsatisfied=None):
    return {"task_id": task_id, "is_valid": is_valid, "unsatisfied_dependencies": unsatisfied or []}

def make_propagation(task_id, affected_tasks=None, impact_score=0):
    return {"task_id": task_id, "affected_tasks": affected_tasks or [], "impact_score": impact_score}

def build_input(execution_id, tasks, constraints, propagations, trace_id="trace-test"):
    return {
        "trace_id": trace_id,
        "execution_id": execution_id,
        "tasks": tasks,
        "constraint_results": constraints,
        "propagation_results": propagations,
    }


# ── edge case 1: multiple root causes ─────────────────────────────────────────

def test_multiple_root_causes():
    """
    Two independent blocked chains. Bottleneck = T3 (score 8).
    Top-level root_cause = T3's root cause = T3.
    """
    input_data = build_input(
        "exec-multi-root",
        tasks=[make_task("T1"), make_task("T2", ["T1"]), make_task("T3"), make_task("T4", ["T3"])],
        constraints=[
            make_constraint("T1", False),
            make_constraint("T2", False, ["T1"]),
            make_constraint("T3", False),
            make_constraint("T4", False, ["T3"]),
        ],
        propagations=[
            make_propagation("T1", ["T2"], impact_score=3),
            make_propagation("T2", [],     impact_score=1),
            make_propagation("T3", ["T4"], impact_score=8),
            make_propagation("T4", [],     impact_score=2),
        ],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] == "T3"
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:T3"
    assert result["impact_score"] == 8
    assert result["severity"] == "MEDIUM"
    assert result["trace_id"] == "trace-test"


# ── edge case 2: deep dependency chain ────────────────────────────────────────

def test_deep_dependency_chain():
    """T5->T4->T3->T2->T1. T1 is root cause. Bottleneck = T1 (score 10)."""
    input_data = build_input(
        "exec-deep-chain",
        tasks=[make_task("T1"), make_task("T2", ["T1"]), make_task("T3", ["T2"]),
               make_task("T4", ["T3"]), make_task("T5", ["T4"])],
        constraints=[
            make_constraint("T1", False),
            make_constraint("T2", False, ["T1"]),
            make_constraint("T3", False, ["T2"]),
            make_constraint("T4", False, ["T3"]),
            make_constraint("T5", False, ["T4"]),
        ],
        propagations=[
            make_propagation("T1", ["T2", "T3", "T4", "T5"], impact_score=10),
            make_propagation("T2", ["T3", "T4", "T5"],       impact_score=7),
            make_propagation("T3", ["T4", "T5"],             impact_score=4),
            make_propagation("T4", ["T5"],                   impact_score=2),
            make_propagation("T5", [],                       impact_score=0),
        ],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] == "T1"
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1"
    assert result["impact_score"] == 10
    assert result["severity"] == "HIGH"


# ── edge case 3: disconnected blocked components ──────────────────────────────

def test_disconnected_blocked_components():
    """Two isolated blocked subgraphs. Bottleneck = B1 (score 9)."""
    input_data = build_input(
        "exec-disconnected",
        tasks=[make_task("A1"), make_task("A2", ["A1"]), make_task("B1"), make_task("B2", ["B1"])],
        constraints=[
            make_constraint("A1", False),
            make_constraint("A2", False, ["A1"]),
            make_constraint("B1", False),
            make_constraint("B2", False, ["B1"]),
        ],
        propagations=[
            make_propagation("A1", ["A2"], impact_score=5),
            make_propagation("A2", [],     impact_score=1),
            make_propagation("B1", ["B2"], impact_score=9),
            make_propagation("B2", [],     impact_score=2),
        ],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] == "B1"
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:B1"
    assert result["impact_score"] == 9
    assert result["severity"] == "MEDIUM"


# ── edge case 4: no blocked tasks ─────────────────────────────────────────────

def test_no_blocked_tasks():
    """All tasks valid. No bottleneck."""
    input_data = build_input(
        "exec-no-blocked",
        tasks=[make_task("T1"), make_task("T2", ["T1"])],
        constraints=[make_constraint("T1", True), make_constraint("T2", True)],
        propagations=[make_propagation("T1", ["T2"], impact_score=5), make_propagation("T2", [], impact_score=0)],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] is None
    assert result["resolution_signal"] is None
    assert result["impact_score"] == 0
    assert result["severity"] == "LOW"


# ── edge case 5: all tasks blocked ────────────────────────────────────────────

def test_all_tasks_blocked():
    """Every task invalid. Bottleneck = T2 (score 7)."""
    input_data = build_input(
        "exec-all-blocked",
        tasks=[make_task("T1"), make_task("T2"), make_task("T3")],
        constraints=[make_constraint("T1", False), make_constraint("T2", False), make_constraint("T3", False)],
        propagations=[
            make_propagation("T1", ["T2", "T3"], impact_score=4),
            make_propagation("T2", ["T3"],        impact_score=7),
            make_propagation("T3", [],            impact_score=1),
        ],
    )
    result = analyze_blockage(input_data)

    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:T2"
    assert result["impact_score"] == 7
    assert result["severity"] == "MEDIUM"


# ── edge case 6: circular dependency ─────────────────────────────────────────

def test_circular_dependency():
    """T1 <-> T2 circular. Must not loop. Output deterministic."""
    input_data = build_input(
        "exec-circular",
        tasks=[make_task("T1", ["T2"]), make_task("T2", ["T1"])],
        constraints=[make_constraint("T1", False), make_constraint("T2", False)],
        propagations=[
            make_propagation("T1", ["T2"], impact_score=5),
            make_propagation("T2", ["T1"], impact_score=5),
        ],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] in ("T1", "T2")
    assert result["resolution_signal"].startswith("UNBLOCK_DEPENDENCY:")
    assert result["impact_score"] == 5
    assert result["severity"] == "MEDIUM"


# ── edge case 7: self dependency ──────────────────────────────────────────────

def test_self_dependency():
    """T1 depends on itself. Root cause = T1."""
    input_data = build_input(
        "exec-self-dep",
        tasks=[make_task("T1", ["T1"])],
        constraints=[make_constraint("T1", False)],
        propagations=[make_propagation("T1", [], impact_score=3)],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] == "T1"
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1"
    assert result["impact_score"] == 3
    assert result["severity"] == "MEDIUM"


# ── edge case 8: missing dependency ──────────────────────────────────────────

def test_missing_dependency():
    """T2 depends on GHOST (not in task list). Root cause = GHOST."""
    input_data = build_input(
        "exec-missing-dep",
        tasks=[make_task("T2", ["GHOST"])],
        constraints=[make_constraint("T2", False, ["GHOST"])],
        propagations=[make_propagation("T2", [], impact_score=6)],
    )
    result = analyze_blockage(input_data)

    assert result["root_cause"] == "GHOST"
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:GHOST"
    assert result["impact_score"] == 6
    assert result["severity"] == "MEDIUM"


# ── output contract shape ─────────────────────────────────────────────────────

def test_output_has_exactly_tantra_keys():
    """Output must have exactly the 7 TANTRA keys."""
    input_data = build_input(
        "exec-shape",
        tasks=[make_task("T1")],
        constraints=[make_constraint("T1", False)],
        propagations=[make_propagation("T1", [], impact_score=5)],
        trace_id="trace-shape",
    )
    result = analyze_blockage(input_data)
    assert set(result.keys()) == {
        "trace_id", "execution_id", "root_cause", "resolution_signal",
        "impact_score", "severity", "timestamp"
    }
