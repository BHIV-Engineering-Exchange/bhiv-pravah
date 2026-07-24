"""
Tests for Phase 6 — Severity Mapping (deterministic, contract-bound)

Severity rules:
  LOW    → impact_score < 3
  MEDIUM → 3 <= impact_score < 10
  HIGH   → impact_score >= 10
"""

from analyzer.output_structurer import _severity

# ── tests ─────────────────────────────────────────────────────────────────────

def test_severity_zero():
    assert _severity(0) == "LOW"

def test_severity_one():
    assert _severity(1) == "LOW"

def test_severity_two():
    assert _severity(2) == "LOW"

def test_severity_three_is_medium():
    assert _severity(3) == "MEDIUM"

def test_severity_nine_is_medium():
    assert _severity(9) == "MEDIUM"

def test_severity_ten_is_high():
    assert _severity(10) == "HIGH"

def test_severity_large():
    assert _severity(999) == "HIGH"

def test_severity_float_medium():
    assert _severity(5.5) == "MEDIUM"

def test_severity_float_low():
    assert _severity(2.9) == "LOW"

def test_severity_float_high():
    assert _severity(10.0) == "HIGH"

def test_severity_determinism():
    """Same input → identical output on repeated calls."""
    for score in [0, 1, 2, 3, 9, 10, 100]:
        assert _severity(score) == _severity(score)
