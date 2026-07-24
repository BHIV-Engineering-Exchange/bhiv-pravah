"""
Tests for Phase 3 — Bottleneck Detection
"""

from analyzer.bottleneck_detector import detect_bottleneck

# ── helpers ───────────────────────────────────────────────────────────────────

def make_propagation(task_id, affected_tasks=None, impact_score=0):
    return {
        "task_id": task_id,
        "affected_tasks": affected_tasks or [],
        "impact_score": impact_score,
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_no_blocked_tasks():
    """No blocked tasks -> None returned"""
    result = detect_bottleneck([], [make_propagation("T1", impact_score=10)])
    assert result is None


def test_single_blocked_task():
    """Only one blocked task -> it is the bottleneck"""
    propagation = [make_propagation("T1", ["T2", "T3"], impact_score=5)]
    result = detect_bottleneck(["T1"], propagation)
    assert result["task_id"] == "T1"
    assert result["impact_score"] == 5
    assert result["affected_tasks"] == ["T2", "T3"]


def test_highest_impact_score_wins():
    """Blocked task with highest impact_score is the bottleneck"""
    propagation = [
        make_propagation("T1", ["T2"], impact_score=3),
        make_propagation("T2", ["T3", "T4"], impact_score=9),
        make_propagation("T3", [], impact_score=1),
    ]
    result = detect_bottleneck(["T1", "T2", "T3"], propagation)
    assert result["task_id"] == "T2"
    assert result["impact_score"] == 9


def test_only_blocked_tasks_considered():
    """Non-blocked task with higher score must NOT be chosen"""
    propagation = [
        make_propagation("T1", impact_score=100),  # T1 is NOT blocked
        make_propagation("T2", impact_score=5),    # T2 IS blocked
    ]
    result = detect_bottleneck(["T2"], propagation)
    assert result["task_id"] == "T2"
    assert result["impact_score"] == 5


def test_tie_break_lowest_task_id():
    """Equal impact scores -> lowest task_id wins (deterministic)"""
    propagation = [
        make_propagation("T2", impact_score=7),
        make_propagation("T1", impact_score=7),
    ]
    result = detect_bottleneck(["T1", "T2"], propagation)
    assert result["task_id"] == "T1"


def test_missing_from_propagation_defaults_zero():
    """Blocked task not in propagation_results -> impact_score defaults to 0"""
    propagation = [make_propagation("T2", impact_score=4)]
    result = detect_bottleneck(["T1", "T2"], propagation)
    assert result["task_id"] == "T2"
    assert result["impact_score"] == 4


def test_all_zero_impact_scores():
    """All blocked tasks have 0 impact -> tie-break by lowest task_id"""
    propagation = [
        make_propagation("T3", impact_score=0),
        make_propagation("T1", impact_score=0),
        make_propagation("T2", impact_score=0),
    ]
    result = detect_bottleneck(["T1", "T2", "T3"], propagation)
    assert result["task_id"] == "T1"


def test_affected_tasks_sorted():
    """affected_tasks in result must be sorted for determinism"""
    propagation = [make_propagation("T1", ["T4", "T2", "T3"], impact_score=5)]
    result = detect_bottleneck(["T1"], propagation)
    assert result["affected_tasks"] == ["T2", "T3", "T4"]


def test_determinism():
    """Same input -> identical output on repeated calls"""
    propagation = [
        make_propagation("T1", ["T2"], impact_score=8),
        make_propagation("T2", ["T3"], impact_score=3),
    ]
    r1 = detect_bottleneck(["T1", "T2"], propagation)
    r2 = detect_bottleneck(["T1", "T2"], propagation)
    assert r1 == r2


