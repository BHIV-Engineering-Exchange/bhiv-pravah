"""
Tests for Phase 1 — Blocked Task Detection
"""

from analyzer.blocked_task_detector import detect_blocked_tasks

# ── helpers ──────────────────────────────────────────────────────────────────

def make_constraint(task_id, is_valid, unsatisfied=None):
    return {
        "task_id": task_id,
        "is_valid": is_valid,
        "unsatisfied_dependencies": unsatisfied or []
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_no_blocked_tasks():
    """All tasks valid → empty list"""
    results = [
        make_constraint("T1", True),
        make_constraint("T2", True),
    ]
    assert detect_blocked_tasks(results) == []


def test_all_tasks_blocked():
    """All tasks invalid → all returned sorted"""
    results = [
        make_constraint("T3", False),
        make_constraint("T1", False),
        make_constraint("T2", False),
    ]
    assert detect_blocked_tasks(results) == ["T1", "T2", "T3"]


def test_mixed_valid_invalid():
    """Only invalid tasks returned"""
    results = [
        make_constraint("T1", True),
        make_constraint("T2", False, ["T1"]),
        make_constraint("T3", True),
        make_constraint("T4", False, ["T3"]),
    ]
    assert detect_blocked_tasks(results) == ["T2", "T4"]


def test_single_blocked_task():
    """Single blocked task"""
    results = [make_constraint("T1", False)]
    assert detect_blocked_tasks(results) == ["T1"]


def test_single_valid_task():
    """Single valid task → empty"""
    results = [make_constraint("T1", True)]
    assert detect_blocked_tasks(results) == []


def test_empty_constraint_results():
    """No constraint results → empty list"""
    assert detect_blocked_tasks([]) == []


def test_output_is_sorted():
    """Output must always be sorted regardless of input order"""
    results = [
        make_constraint("T10", False),
        make_constraint("T2",  False),
        make_constraint("T1",  False),
    ]
    output = detect_blocked_tasks(results)
    assert output == sorted(output)


def test_determinism():
    """Same input → identical output on repeated calls"""
    results = [
        make_constraint("T3", False),
        make_constraint("T1", True),
        make_constraint("T2", False),
    ]
    assert detect_blocked_tasks(results) == detect_blocked_tasks(results)


