"""
Layer Contract Tests — covers all uncovered fail-closed branches

Targets:
  rajya.py       L18 (FAIL status), L22 (missing trace_id), L24 (trace_id mismatch)
  sarathi.py     L18 (missing trace_id)
  core.py        L18 (missing trace_id)
  bucket.py      L23 (missing trace_id)
  root_cause_tracer.py  L47 (dep not in known_tasks → immediate return),
                        L74 (unknown dep found during BFS → immediate return)
"""

import pytest

from analyzer.root_cause_tracer import trace_root_causes
from tantra import bucket, core, rajya, sarathi
from tantra.bucket import write as bucket_write


@pytest.fixture(autouse=True)
def reset_bucket():
    bucket.clear()
    yield
    bucket.clear()


# ── rajya ─────────────────────────────────────────────────────────────────────

def test_rajya_rejects_keshav_fail_status():
    """RAJYA must raise on KESHAV FAIL output (L18)."""
    with pytest.raises(ValueError, match="upstream KESHAV failure"):
        rajya.consume({"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": ""}, "")


def test_rajya_rejects_missing_trace_id():
    """RAJYA must raise when trace_id absent from keshav_output (L22)."""
    with pytest.raises(ValueError, match="missing trace_id"):
        rajya.consume({"execution_id": "e1"}, "some-trace")


def test_rajya_rejects_trace_id_mismatch():
    """RAJYA must raise on trace_id mismatch (L24)."""
    keshav_out = {
        "trace_id": "trace-A",
        "execution_id": "e1",
        "root_cause": None,
        "resolution_signal": None,
        "impact_score": 0,
        "severity": "LOW",
        "timestamp": "2025-01-01T00:00:00Z",
    }
    with pytest.raises(ValueError, match="trace_id mismatch"):
        rajya.consume(keshav_out, "trace-B")


# ── sarathi ───────────────────────────────────────────────────────────────────

def test_sarathi_rejects_missing_trace_id():
    """Sarathi must raise when trace_id is absent (L18)."""
    with pytest.raises(ValueError, match="missing trace_id"):
        sarathi.enforce({"resolution_signal": "UNBLOCK_DEPENDENCY:T1"})


# ── core ──────────────────────────────────────────────────────────────────────

def test_core_rejects_missing_trace_id():
    """Core must raise when trace_id is absent (L18)."""
    with pytest.raises(ValueError, match="missing trace_id"):
        core.execute({"action": "ENFORCE:UNBLOCK_DEPENDENCY:T1"})


# ── bucket ────────────────────────────────────────────────────────────────────

def test_bucket_rejects_missing_trace_id():
    """Bucket write must raise when trace_id is absent (L23)."""
    with pytest.raises(ValueError, match="missing trace_id"):
        bucket_write({"executed": True}, {"root_cause": "T1"})
    assert len(bucket.all_trace_ids()) == 0


# ── root_cause_tracer ─────────────────────────────────────────────────────────

def test_root_cause_tracer_missing_dep_not_in_known_tasks():
    """
    L47: dep listed in unsatisfied_dependencies but absent from task list
    → returned immediately as root cause without BFS.
    """
    tasks = [{"task_id": "T2", "depends_on": ["GHOST"]}]
    constraints = [{"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["GHOST"]}]
    result = trace_root_causes(["T2"], tasks, constraints)
    assert result["T2"] == "GHOST"


def test_root_cause_tracer_bfs_hits_unknown_dep():
    """
    L74: during BFS traversal an unknown dep (not in known_tasks) is encountered
    → returned immediately as root cause.
    """
    # T1 is invalid, its unsatisfied dep is T_UNKNOWN (not in task list)
    # T2 depends on T1 (invalid) → BFS from T1 finds T_UNKNOWN
    tasks = [
        {"task_id": "T1", "depends_on": ["T_UNKNOWN"]},
        {"task_id": "T2", "depends_on": ["T1"]},
    ]
    constraints = [
        {"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": ["T_UNKNOWN"]},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
    ]
    result = trace_root_causes(["T2"], tasks, constraints)
    assert result["T2"] == "T_UNKNOWN"


def test_root_cause_tracer_unsatisfied_dep_is_valid_in_known_tasks():
    """L47: unsatisfied dep IS in known_tasks AND IS valid -> returned directly (no BFS)."""
    tasks = [
        {"task_id": "T1", "depends_on": []},
        {"task_id": "T2", "depends_on": ["T1"]},
    ]
    constraints = [
        {"task_id": "T1", "is_valid": True, "unsatisfied_dependencies": []},
        {"task_id": "T2", "is_valid": False, "unsatisfied_dependencies": ["T1"]},
    ]
    result = trace_root_causes(["T2"], tasks, constraints)
    assert result["T2"] == "T1"
