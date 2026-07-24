from engine.guard import should_execute


def test_guard_allows_workflow():
    assert should_execute("workflow") is True


def test_guard_blocks_non_workflow():
    assert should_execute("respond") is False
    assert should_execute("task") is False
    assert should_execute("insight") is False
    assert should_execute("fallback") is False
