import asyncio
import pytest
from phd_agent.api import deps
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.profile import UserProfile
from phd_agent.llm.mock import MockLLMClient


@pytest.fixture(autouse=True)
def reset_cache(tmp_path):
    deps._repo = JsonFileRepository(tmp_path)
    deps.invalidate_profile_cache()
    yield
    deps.invalidate_profile_cache()


def test_run_turn_uses_profile_llm():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    repo = deps.get_repo()
    asyncio.run(repo.save_profile(UserProfile(
        llm_provider="openai", base_url="https://x",
        api_key="sk-test1234", model_name="my-test-model",
    )))

    received_model = []

    async def factory():
        tracking_llm = MockLLMClient(responses=["ok"])
        original_chat = tracking_llm.chat
        async def tracking_chat(messages, *, tools=None, budget=4000, model=""):
            received_model.append(model)
            return await original_chat(messages, tools=tools, budget=budget, model=model)
        tracking_llm.chat = tracking_chat
        return tracking_llm, "factory-model"

    default_llm = MockLLMClient(responses=["default"])
    wrapper = AgentWrapper(reg, bus, default_llm)
    runtime = ToolRuntime(reg, default_llm, bus, repo, wrapper=wrapper, model="mock",
                           llm_factory=factory)
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)

    async def go():
        async for _ in runtime.run_turn(session, "hi"):
            pass
    asyncio.run(go())
    assert received_model[0] == "factory-model"


def test_run_turn_with_no_profile_falls_back_to_default():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    repo = deps.get_repo()
    llm = MockLLMClient(responses=["ok-mock"])
    wrapper = AgentWrapper(reg, bus, llm)
    runtime = ToolRuntime(reg, llm, bus, repo, wrapper=wrapper, model="mock")
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)

    async def go():
        async for _ in runtime.run_turn(session, "hi"):
            pass
    asyncio.run(go())
    assert llm.call_count == 1
    assert session.messages[-1].content == "ok-mock"