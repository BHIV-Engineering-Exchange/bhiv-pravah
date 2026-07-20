"""
Product Core v1 Extension - Next Task Generator Tests
Tests for deterministic rule-based task assignment.
"""
import pytest
from datetime import datetime
from app.services.next_task_generator import NextTaskGenerator, TaskType


def test_correction_task_assignment():
    """Test score < 50 assigns CORRECTION task"""
    result = NextTaskGenerator.generate(score=30, previous_submission_id="sub-001")
    
    assert result["task_type"] == TaskType.CORRECTION.value
    assert result["difficulty"] == "beginner"
    assert result["focus_area"] == "Requirements Engineering"
    assert result["previous_submission_id"] == "sub-001"
    assert "correction" in result["reason"].lower()


def test_reinforcement_task_assignment():
    """Test 50 <= score < 80 assigns REINFORCEMENT task"""
    result = NextTaskGenerator.generate(score=65, previous_submission_id="sub-002")
    
    assert result["task_type"] == TaskType.REINFORCEMENT.value
    assert result["difficulty"] == "intermediate"
    assert result["focus_area"] == "Technical Documentation"
    assert result["previous_submission_id"] == "sub-002"
    assert "reinforcement" in result["reason"].lower()


def test_advancement_task_assignment():
    """Test score >= 80 assigns ADVANCEMENT task"""
    result = NextTaskGenerator.generate(score=85, previous_submission_id="sub-003")
    
    assert result["task_type"] == TaskType.ADVANCEMENT.value
    assert result["difficulty"] == "advanced"
    assert result["focus_area"] == "System Architecture"
    assert result["previous_submission_id"] == "sub-003"
    assert "advancement" in result["reason"].lower()


def test_threshold_boundaries():
    """Test exact threshold boundaries"""
    # Score 49 -> CORRECTION
    result_49 = NextTaskGenerator.generate(score=49, previous_submission_id="sub-004")
    assert result_49["task_type"] == TaskType.CORRECTION.value
    
    # Score 50 -> REINFORCEMENT
    result_50 = NextTaskGenerator.generate(score=50, previous_submission_id="sub-005")
    assert result_50["task_type"] == TaskType.REINFORCEMENT.value
    
    # Score 79 -> REINFORCEMENT
    result_79 = NextTaskGenerator.generate(score=79, previous_submission_id="sub-006")
    assert result_79["task_type"] == TaskType.REINFORCEMENT.value
    
    # Score 80 -> ADVANCEMENT
    result_80 = NextTaskGenerator.generate(score=80, previous_submission_id="sub-007")
    assert result_80["task_type"] == TaskType.ADVANCEMENT.value


def test_deterministic_assignment():
    """Test same score always yields same task type"""
    results = []
    for i in range(10):
        result = NextTaskGenerator.generate(score=60, previous_submission_id=f"sub-{i}")
        results.append(result["task_type"])
    
    # All should be identical
    assert len(set(results)) == 1
    assert results[0] == TaskType.REINFORCEMENT.value


def test_output_structure():
    """Test output contains all required fields"""
    result = NextTaskGenerator.generate(score=70, previous_submission_id="sub-test")
    
    required_fields = [
        "task_type", "previous_submission_id", "title", "objective",
        "focus_area", "difficulty", "reason", "assigned_timestamp"
    ]
    
    for field in required_fields:
        assert field in result
    
    # Verify timestamp is datetime
    assert isinstance(result["assigned_timestamp"], datetime)


def test_get_thresholds():
    """Test threshold retrieval"""
    thresholds = NextTaskGenerator.get_thresholds()
    
    assert thresholds["fail_threshold"] == 50
    assert thresholds["pass_threshold"] == 80


def test_rules_version():
    """Test rules version tracking"""
    version = NextTaskGenerator.get_rules_version()
    assert version == "1.0.0"


def test_edge_cases():
    """Test edge cases (0, 100)"""
    # Score 0
    result_0 = NextTaskGenerator.generate(score=0, previous_submission_id="sub-min")
    assert result_0["task_type"] == TaskType.CORRECTION.value
    
    # Score 100
    result_100 = NextTaskGenerator.generate(score=100, previous_submission_id="sub-max")
    assert result_100["task_type"] == TaskType.ADVANCEMENT.value


def test_task_definitions_complete():
    """Test all task definitions are complete"""
    for task_type in TaskType:
        task_def = NextTaskGenerator.TASK_RULES[task_type]
        
        assert "title" in task_def
        assert "objective" in task_def
        assert "focus_area" in task_def
        assert "difficulty" in task_def
        assert "reason" in task_def
        
        assert len(task_def["title"]) > 0
        assert len(task_def["objective"]) > 0
