from engine.engine import execute_engine


def test_missing_action_type():
    result = execute_engine({})
    assert result["success"] is False
    assert result["error_code"] == "missing_action_type"


def test_unsupported_action_type():
    result = execute_engine({"action_type": "email"})
    assert result["success"] is False
    assert result["error_code"] == "unsupported_action_type"


def test_task_routing():
    result = execute_engine({
        "action_type": "task",
        "title": "Test task"
    })
    assert result["success"] is True
    assert result["title"] == "Test task"


def test_reminder_routing():
    result = execute_engine({
        "action_type": "reminder",
        "message": "Test reminder",
        "time": "2025-01-01T10:00:00"
    })
    assert result["success"] is True
    assert result["message"] == "Test reminder"


def test_meeting_routing():
    result = execute_engine({
        "action_type": "meeting",
        "title": "Test meeting",
        "participants": ["a@test.com"],
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00"
    })
    assert result["success"] is True
    assert result["title"] == "Test meeting"


def test_info_routing():
    result = execute_engine({
        "action_type": "info",
        "query": "test_query"
    })
    assert result["success"] is True
    assert "test_query" in result["data"]
