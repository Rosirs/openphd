from phd_agent.core.state import GlobalState

def test_globalstate_defaults():
    state = GlobalState(user_id="u1")
    assert state.user_id == "u1"
    assert state.user_background == {}
    assert state.active_pipeline == []
    assert state.current_step == 0
    assert state.dynamic_storage == {}
    assert state.error_log == []
    assert state.status == "idle"

def test_globalstate_status_literals():
    # Pydantic enforces Literal; an invalid status must raise
    import pytest
    with pytest.raises(ValueError):
        GlobalState(user_id="u1", status="nonsense")

def test_globalstate_dynamic_storage_isolated_per_instance():
    a = GlobalState(user_id="a")
    b = GlobalState(user_id="b")
    a.dynamic_storage["k"] = 1
    assert "k" not in b.dynamic_storage
