"""
Tests for Phase 5 — TANTRA Output Structuring

TANTRA contract keys: trace_id, execution_id, root_cause, resolution_signal,
                      impact_score, severity, timestamp
"""

import re

from analyzer.output_structurer import structure_output

# ── helpers ───────────────────────────────────────────────────────────────────

def make_bottleneck(task_id, impact_score, affected_tasks=None):
    return {"task_id": task_id, "impact_score": impact_score, "affected_tasks": affected_tasks or []}


# ── tests ─────────────────────────────────────────────────────────────────────

def test_output_contract_keys():
    """Output must have exactly TANTRA keys."""
    result = structure_output(
        trace_id="trace-abc",
        execution_id="exec-1",
        root_causes={"T1": "T1"},
        bottleneck=make_bottleneck("T1", 5),
        actions=[{"signal": "UNBLOCK_DEPENDENCY:T1", "target": "T1", "expected_unblock": 1}],
    )
    assert set(result.keys()) == {
        "trace_id", "execution_id", "root_cause", "resolution_signal",
        "impact_score", "severity", "timestamp"
    }


def test_trace_id_passed_through_unchanged():
    """trace_id from input must appear unchanged in output."""
    result = structure_output(
        trace_id="upstream-trace-xyz",
        execution_id="exec-1",
        root_causes={"T1": "T1"},
        bottleneck=make_bottleneck("T1", 5),
        actions=[],
    )
    assert result["trace_id"] == "upstream-trace-xyz"


def test_resolution_signal_format():
    """resolution_signal must be UNBLOCK_DEPENDENCY:<task_id>"""
    result = structure_output(
        trace_id="t1",
        execution_id="exec-1",
        root_causes={"T1": "T1"},
        bottleneck=make_bottleneck("T1", 5),
        actions=[{"signal": "UNBLOCK_DEPENDENCY:T1", "target": "T1", "expected_unblock": 1}],
    )
    assert result["resolution_signal"] == "UNBLOCK_DEPENDENCY:T1"


def test_impact_score_at_top_level():
    """impact_score must be present at top level."""
    result = structure_output(
        trace_id="t1",
        execution_id="exec-1",
        root_causes={"T1": "T1"},
        bottleneck=make_bottleneck("T1", 7),
        actions=[],
    )
    assert result["impact_score"] == 7


def test_severity_low():
    """impact_score < 3 → severity LOW"""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=make_bottleneck("T1", 2), actions=[]
    )
    assert result["severity"] == "LOW"


def test_severity_medium_lower_bound():
    """impact_score == 3 → severity MEDIUM"""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=make_bottleneck("T1", 3), actions=[]
    )
    assert result["severity"] == "MEDIUM"


def test_severity_medium_upper_bound():
    """impact_score == 9 → severity MEDIUM"""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=make_bottleneck("T1", 9), actions=[]
    )
    assert result["severity"] == "MEDIUM"


def test_severity_high():
    """impact_score >= 10 → severity HIGH"""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=make_bottleneck("T1", 10), actions=[]
    )
    assert result["severity"] == "HIGH"


def test_severity_zero_is_low():
    """impact_score == 0 (no bottleneck) → severity LOW"""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=None, actions=[]
    )
    assert result["severity"] == "LOW"
    assert result["impact_score"] == 0


def test_timestamp_iso8601():
    """timestamp must be ISO-8601 UTC format."""
    result = structure_output(
        trace_id="t1", execution_id="e", root_causes={}, bottleneck=None, actions=[]
    )
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", result["timestamp"])


def test_no_bottleneck_nulls():
    """No bottleneck → root_cause None, resolution_signal None, impact_score 0."""
    result = structure_output(
        trace_id="t1", execution_id="exec-empty", root_causes={}, bottleneck=None, actions=[]
    )
    assert result["root_cause"] is None
    assert result["resolution_signal"] is None
    assert result["impact_score"] == 0


def test_execution_id_preserved():
    """execution_id from input must pass through unchanged."""
    result = structure_output(
        trace_id="t1", execution_id="run-xyz-999", root_causes={}, bottleneck=None, actions=[]
    )
    assert result["execution_id"] == "run-xyz-999"


def test_determinism_json_identical():
    """Serialized JSON output must be byte-for-byte identical across runs (excluding timestamp)."""
    kwargs = dict(
        trace_id="trace-det",
        execution_id="exec-det",
        root_causes={"T1": "T1"},
        bottleneck=make_bottleneck("T1", 10, ["T2", "T3"]),
        actions=[{"signal": "UNBLOCK_DEPENDENCY:T1", "target": "T1", "expected_unblock": 2}],
    )
    r1 = structure_output(**kwargs)
    r2 = structure_output(**kwargs)
    # all fields except timestamp must be identical
    for key in ("trace_id", "execution_id", "root_cause", "resolution_signal", "impact_score", "severity"):
        assert r1[key] == r2[key]
