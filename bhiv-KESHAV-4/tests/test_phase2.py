"""
Tests for Phase 2 — Root Cause Tracing
"""

from analyzer.root_cause_tracer import trace_root_causes

# ── helpers ───────────────────────────────────────────────────────────────────

def make_task(task_id, depends_on=None):
    return {"task_id": task_id, "depends_on": depends_on or []}

def make_constraint(task_id, is_valid, unsatisfied=None):
    return {"task_id": task_id, "is_valid": is_valid, "unsatisfied_dependencies": unsatisfied or []}


# ── tests ─────────────────────────────────────────────────────────────────────

def test_task_is_own_root_cause():
    """
    T1 is blocked, has no dependencies → T1 is its own root cause
    """
    tasks = [make_task("T1")]
    constraints = [make_constraint("T1", False)]
    result = trace_root_causes(["T1"], tasks, constraints)
    assert result == {"T1": "T1"}


def test_direct_dependency_is_root_cause():
    """
    T2 depends on T1. T1 is invalid → T1 is root cause of T2
    """
    tasks = [make_task("T1"), make_task("T2", ["T1"])]
    constraints = [
        make_constraint("T1", False),
        make_constraint("T2", False, ["T1"]),
    ]
    result = trace_root_causes(["T2"], tasks, constraints)
    assert result == {"T2": "T1"}


def test_deep_dependency_chain():
    """
    T3 → T2 → T1. T1 is invalid → T1 is root cause for both T2 and T3
    """
    tasks = [
        make_task("T1"),
        make_task("T2", ["T1"]),
        make_task("T3", ["T2"]),
    ]
    constraints = [
        make_constraint("T1", False),
        make_constraint("T2", False, ["T1"]),
        make_constraint("T3", False, ["T2"]),
    ]
    result = trace_root_causes(["T2", "T3"], tasks, constraints)
    assert result == {"T2": "T1", "T3": "T1"}


def test_multiple_root_causes():
    """
    T3 → T1 (invalid), T4 → T2 (invalid) → two separate root causes
    """
    tasks = [
        make_task("T1"),
        make_task("T2"),
        make_task("T3", ["T1"]),
        make_task("T4", ["T2"]),
    ]
    constraints = [
        make_constraint("T1", False),
        make_constraint("T2", False),
        make_constraint("T3", False, ["T1"]),
        make_constraint("T4", False, ["T2"]),
    ]
    result = trace_root_causes(["T3", "T4"], tasks, constraints)
    assert result == {"T3": "T1", "T4": "T2"}


def test_missing_dependency_is_root_cause():
    """
    T2 depends on T_MISSING which doesn't exist in task list → T_MISSING is root cause
    """
    tasks = [make_task("T2", ["T_MISSING"])]
    constraints = [make_constraint("T2", False, ["T_MISSING"])]
    result = trace_root_causes(["T2"], tasks, constraints)
    assert result == {"T2": "T_MISSING"}


def test_disconnected_blocked_components():
    """
    Two completely separate blocked chains with no shared nodes
    """
    tasks = [
        make_task("A1"),
        make_task("A2", ["A1"]),
        make_task("B1"),
        make_task("B2", ["B1"]),
    ]
    constraints = [
        make_constraint("A1", False),
        make_constraint("A2", False, ["A1"]),
        make_constraint("B1", False),
        make_constraint("B2", False, ["B1"]),
    ]
    result = trace_root_causes(["A2", "B2"], tasks, constraints)
    assert result == {"A2": "A1", "B2": "B1"}


def test_circular_dependency_no_infinite_loop():
    """
    T1 → T2 → T1 (circular). Must not loop forever.
    Both are blocked → each becomes its own root cause (no valid upstream found)
    """
    tasks = [
        make_task("T1", ["T2"]),
        make_task("T2", ["T1"]),
    ]
    constraints = [
        make_constraint("T1", False),
        make_constraint("T2", False),
    ]
    result = trace_root_causes(["T1", "T2"], tasks, constraints)
    # circular: traversal finds T2 (dep of T1) which is invalid → T2 is root cause of T1
    # traversal finds T1 (dep of T2) which is invalid → T1 is root cause of T2
    assert result["T1"] in ("T1", "T2")
    assert result["T2"] in ("T1", "T2")


def test_determinism():
    """Same input → identical output on repeated calls"""
    tasks = [
        make_task("T1"),
        make_task("T2", ["T1"]),
        make_task("T3", ["T2"]),
    ]
    constraints = [
        make_constraint("T1", False),
        make_constraint("T2", False, ["T1"]),
        make_constraint("T3", False, ["T2"]),
    ]
    r1 = trace_root_causes(["T2", "T3"], tasks, constraints)
    r2 = trace_root_causes(["T2", "T3"], tasks, constraints)
    assert r1 == r2


def test_empty_blocked_list():
    """No blocked tasks → empty dict"""
    tasks = [make_task("T1"), make_task("T2")]
    constraints = [make_constraint("T1", True), make_constraint("T2", True)]
    result = trace_root_causes([], tasks, constraints)
    assert result == {}


