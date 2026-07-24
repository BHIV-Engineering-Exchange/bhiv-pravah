import os
from app.replay_guard import check_and_store, STORE_FILE

def test_persistence_across_restart():
    if os.path.exists(STORE_FILE):
        os.remove(STORE_FILE)

    assert check_and_store("restart-msg") is True
    assert check_and_store("restart-msg") is False
