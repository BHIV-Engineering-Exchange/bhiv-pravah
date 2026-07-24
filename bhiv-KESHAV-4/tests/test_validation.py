"""
Tests for Phase 5 — Failure Mode Enforcement

Invalid input must return:
  { "status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": "" }

Required fields: trace_id (str), execution_id (str)
"""

from analyzer.analyze_blockage import analyze_and_recommend as analyze_blockage

FAIL_RESPONSE = {"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": ""}


def test_missing_trace_id_fails_closed():
    """Missing trace_id must return FAIL response."""
    result = analyze_blockage({
        "execution_id": "exec-1",
        "tasks": [],
        "constraint_results": [],
        "propagation_results": [],
    })
    assert result == FAIL_RESPONSE


def test_missing_execution_id_fails_closed():
    """Missing execution_id must return FAIL response."""
    result = analyze_blockage({
        "trace_id": "trace-1",
        "tasks": [],
        "constraint_results": [],
        "propagation_results": [],
    })
    assert result == FAIL_RESPONSE


def test_non_dict_input_fails_closed():
    """Non-dict input must return FAIL response."""
    result = analyze_blockage("not a dict")
    assert result == FAIL_RESPONSE


def test_wrong_type_execution_id_fails_closed():
    """execution_id of wrong type must return FAIL response."""
    result = analyze_blockage({
        "trace_id": "trace-1",
        "execution_id": 12345,
        "tasks": [],
        "constraint_results": [],
        "propagation_results": [],
    })
    assert result == FAIL_RESPONSE


def test_wrong_type_trace_id_fails_closed():
    """trace_id of wrong type must return FAIL response."""
    result = analyze_blockage({
        "trace_id": 999,
        "execution_id": "exec-1",
        "tasks": [],
        "constraint_results": [],
        "propagation_results": [],
    })
    assert result == FAIL_RESPONSE


def test_valid_minimal_input_passes():
    """Minimal valid input (trace_id + execution_id) must succeed."""
    result = analyze_blockage({
        "trace_id": "trace-valid",
        "execution_id": "exec-valid",
    })
    assert result["execution_id"] == "exec-valid"
    assert result["trace_id"] == "trace-valid"
    assert "status" not in result


def test_trace_id_passed_through_unchanged():
    """trace_id from input must appear unchanged in output."""
    result = analyze_blockage({
        "trace_id": "upstream-trace-abc",
        "execution_id": "exec-1",
    })
    assert result["trace_id"] == "upstream-trace-abc"


def test_optional_fields_default_to_empty():
    """tasks, constraint_results, propagation_results are optional."""
    result = analyze_blockage({"trace_id": "t", "execution_id": "exec-minimal"})
    assert result["execution_id"] == "exec-minimal"
    assert result["impact_score"] == 0
