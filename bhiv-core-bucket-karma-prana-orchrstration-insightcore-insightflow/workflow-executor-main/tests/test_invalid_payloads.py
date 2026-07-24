from engine.engine import execute_engine


def test_task_missing_title():
    result = execute_engine({
        "action_type": "task"
    })
    assert result["success"] is False
    assert result["error_code"] == "missing_task_title"


def test_reminder_missing_fields():
    result = execute_engine({
        "action_type": "reminder",
        "message": "Hello"
    })
    assert result["success"] is False
    assert result["error_code"] == "missing_reminder_fields"


def test_meeting_missing_fields():
    result = execute_engine({
        "action_type": "meeting",
        "title": "Meeting"
    })
    assert result["success"] is False
    assert result["error_code"] == "missing_meeting_fields"


def test_info_missing_query():
    result = execute_engine({
        "action_type": "info"
    })
    assert result["success"] is False
    assert result["error_code"] == "missing_info_query"
