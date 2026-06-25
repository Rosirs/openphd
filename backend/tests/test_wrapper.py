import asyncio
import pytest
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState
from phd_agent.core.contract import AgentContract, BaseAgent

class _Exploder(BaseAgent):
    contract = AgentContract(
        agent_id="exploder", name="E", description="d", category="mock",
        required_fields=set(), output_fields=set(),
    )
    async def run(self, state):
        raise RuntimeError("kaboom")

class _Writer(BaseAgent):
    contract = AgentContract(
        agent_id="writer", name="W", description="d", category="mock",
        required_fields=set(), output_fields={"dynamic_storage.k"},
    )
    async def run(self, state):
        state.dynamic_storage["k"] = "v"
        return state

class _FakeRegistry:
    def __init__(self, m):
        self._m = m
    def load(self, agent_id):
        return self._m[agent_id]()

class _NoopLLM:
    def count_tokens(self, text): return 0

@pytest.mark.asyncio
async def test_wrapper_executes_and_increments_step():
    bus = EventBus()
    reg = _FakeRegistry({"writer": _Writer})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["writer"], current_step=0)
    await w.execute(state, "writer", "run-1", bus)
    assert state.current_step == 1
    assert state.dynamic_storage["k"] == "v"
    assert state.status != "failed"

@pytest.mark.asyncio
async def test_wrapper_isolates_exceptions_and_marks_step():
    bus = EventBus()
    reg = _FakeRegistry({"exploder": _Exploder})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["exploder"], current_step=0)
    await w.execute(state, "exploder", "run-1", bus)
    assert state.current_step == 1
    assert len(state.error_log) == 1
    assert state.error_log[0]["agent_id"] == "exploder"
    assert "kaboom" in state.error_log[0]["error"]

@pytest.mark.asyncio
async def test_wrapper_publishes_event():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    reg = _FakeRegistry({"writer": _Writer})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["writer"])
    await w.execute(state, "writer", "run-1", bus)
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "writer"
    assert event.status == "ok"
