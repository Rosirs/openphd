import pytest
from phd_agent.core.router import CentralRouter
from phd_agent.core.state import GlobalState

@pytest.fixture
def router():
    # No registry needed for pure dispatch logic
    return CentralRouter(registry=None)

def test_dispatch_returns_first_agent_when_step_zero(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b", "c"], current_step=0)
    assert router.dispatch(state) == "a"

def test_dispatch_returns_next_agent_in_sequence(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b", "c"], current_step=1)
    assert router.dispatch(state) == "b"

def test_dispatch_returns_none_when_out_of_bounds(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b"], current_step=2)
    assert router.dispatch(state) is None

def test_dispatch_returns_none_for_empty_pipeline(router):
    state = GlobalState(user_id="u", active_pipeline=[], current_step=0)
    assert router.dispatch(state) is None