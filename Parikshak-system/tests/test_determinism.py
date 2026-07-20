import pytest

def evaluate(input_data):
    # Deterministic mock function representing the pipeline
    score = input_data.get("score", 0)
    return {"status": "PASS" if score >= 80 else "FAIL", "score": score}

def test_determinism():
    input_data = {"score": 85, "sample": "data"}
    # The output MUST be strictly deterministic for identical inputs
    assert evaluate(input_data) == evaluate(input_data)

def test_determinism_fail():
    input_data = {"score": 40, "sample": "data"}
    assert evaluate(input_data) == evaluate(input_data)
