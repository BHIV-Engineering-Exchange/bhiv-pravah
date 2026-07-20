import pytest

def merge_logic(assignment_result, signal_result):
    if assignment_result["status"] == "FAIL":
        return {
            "status": "FAIL",
            "score": assignment_result["accuracy"]
        }
    final_score = assignment_result["accuracy"] + signal_result.get("bonus", 0)
    return {
        "status": "PASS",
        "score": final_score
    }

def test_assignment_authority():
    assignment = {"status": "FAIL", "accuracy": 40}
    signals = {"bonus": 50}

    result = merge_logic(assignment, signals)

    # Signal bonus MUST NOT override a FAIL assignment status
    assert result["status"] == "FAIL"
    assert result["score"] == 40
    
def test_assignment_authority_pass():
    assignment = {"status": "PASS", "accuracy": 80}
    signals = {"bonus": 10}

    result = merge_logic(assignment, signals)

    # Signals CAN enhance a passing score
    assert result["status"] == "PASS"
    assert result["score"] == 90
