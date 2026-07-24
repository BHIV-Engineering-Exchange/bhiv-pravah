from app.replay_guard import check_and_store

def test_first_message_allowed():
    assert check_and_store("msg-1") is True

def test_replay_blocked():
    check_and_store("msg-1")
    assert check_and_store("msg-1") is False
