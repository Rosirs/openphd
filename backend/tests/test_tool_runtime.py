"""Tests for ToolRuntime LLM loop."""
import asyncio
import pytest
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.contract import AgentContract, BaseAgent
from phd_agent.llm.mock import MockLLMClient


class StubAgent(BaseAgent):
    contract = AgentContract(
        agent_id="stub", name="Stub", description="stub agent",
        category="mock", required_fields=set(), output_fields=set(),
    )

    async def run(self, state, **kwargs):
        state.dynamic_storage["stub_ran"] = True
        return state


def test_text_only_response():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(StubAgent.contract, StubAgent)
    repo = JsonFileRepository("/tmp/_test_repo_text")
    llm = MockLLMClient(responses=["final answer"])
    runtime = ToolRuntime(reg, llm, bus, repo)
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)
    events = []
    async def collect():
        async for ev in runtime.run_turn(session, "hi"):
            events.append(ev)
    asyncio.run(collect())
    assert events[-1]["type"] == "message_completed"
    assert events[-1]["content"] == "final answer"
    assert session.messages[-1].role == "assistant"
    assert session.messages[-1].content == "final answer"


def test_tool_call_then_text():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(StubAgent.contract, StubAgent)
    repo = JsonFileRepository("/tmp/_test_repo_tool")
    llm = MockLLMClient(
        responses=["done after stub"],
        tool_calls=[{"id": "tc1", "name": "stub", "args": {}}],
    )
    runtime = ToolRuntime(reg, llm, bus, repo)
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)
    events = []
    async def collect():
        async for ev in runtime.run_turn(session, "go"):
            events.append(ev)
    asyncio.run(collect())
    types = [e["type"] for e in events]
    assert "tool_call_started" in types
    assert "tool_call_completed" in types
    assert "message_completed" in types
    assert state.dynamic_storage["stub_ran"] is True


def test_persistence():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    reg.register(StubAgent.contract, StubAgent)
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        repo = JsonFileRepository(td)
        llm = MockLLMClient(responses=["saved"])
        runtime = ToolRuntime(reg, llm, bus, repo)
        state = GlobalState(user_id="u1")
        session = ChatSession(user_id="u1", conversation_id="c1", state=state)
        async def collect():
            async for _ in runtime.run_turn(session, "hi"):
                pass
        asyncio.run(collect())
        # Re-load and verify
        async def load():
            return await repo.load_conversation("u1", "c1")
        loaded = asyncio.run(load())
        assert loaded is not None
        assert len(loaded.messages) == 2  # user + assistant
        assert loaded.messages[1].content == "saved"
