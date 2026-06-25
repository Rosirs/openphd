"""Tests for CompositeAgent (LLM-driven nested agent)."""
import asyncio
import pytest
from phd_agent.core.composite_agent import CompositeAgent
from phd_agent.core.composite import CompositeToolDefinition
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.contract import AgentContract, BaseAgent
from phd_agent.llm.mock import MockLLMClient


class Sub(BaseAgent):
    contract = AgentContract(
        agent_id="sub", name="Sub", description="sub agent",
        category="mock", required_fields=set(), output_fields=set(),
    )

    async def run(self, state, **kwargs):
        state.dynamic_storage["sub_ran"] = True
        return state


def test_composite_returns_final_answer():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(Sub.contract, Sub)
    llm = MockLLMClient(responses=["final summary"])
    wrapper = AgentWrapper(reg, bus, llm)
    definition = CompositeToolDefinition(
        tool_id="ct", name="CT", description="d", system_prompt="summarize",
        sub_tools=["sub"], owner_user_id="u1",
    )
    agent = CompositeAgent(definition, llm, wrapper, bus)
    state = GlobalState(user_id="u1")
    result = asyncio.run(agent.run(args={"text": "x"}, state=state))
    assert result.success is True
    assert "final summary" in result.llm_context


def test_composite_invokes_sub_tool_then_returns():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(Sub.contract, Sub)
    llm = MockLLMClient(
        responses=["final after sub"],
        tool_calls=[{"id": "tc1", "name": "sub", "args": {}}],
    )
    wrapper = AgentWrapper(reg, bus, llm)
    definition = CompositeToolDefinition(
        tool_id="ct", name="CT", description="d", system_prompt="go",
        sub_tools=["sub"], owner_user_id="u1",
    )
    agent = CompositeAgent(definition, llm, wrapper, bus)
    state = GlobalState(user_id="u1")
    result = asyncio.run(agent.run(args={}, state=state))
    assert result.success is True
    assert state.dynamic_storage["sub_ran"] is True
    assert "final after sub" in result.llm_context


def test_composite_blocks_nested_composite_call():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(Sub.contract, Sub)
    # Try to call "sub" via sub-llm but the registry has a composite "sub" registered
    composite_def = CompositeToolDefinition(
        tool_id="sub", name="Sub", description="d", system_prompt="",
        sub_tools=[], owner_user_id="u1",
    )
    reg.load_composites([composite_def])
    llm = MockLLMClient(
        responses=["after block"],
        tool_calls=[{"id": "tc1", "name": "sub", "args": {}}],
    )
    wrapper = AgentWrapper(reg, bus, llm)
    outer_def = CompositeToolDefinition(
        tool_id="outer", name="O", description="d", system_prompt="go",
        sub_tools=["sub"], owner_user_id="u1",
    )
    agent = CompositeAgent(outer_def, llm, wrapper, bus)
    state = GlobalState(user_id="u1")
    result = asyncio.run(agent.run(args={}, state=state))
    # The composite call was blocked, so sub_ran should be False
    assert state.dynamic_storage.get("sub_ran") is not True
    assert result.success is True
