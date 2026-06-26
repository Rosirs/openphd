"""Regression tests: /chat must resolve LLM through the user profile, not a hardcoded mock.

Background: previously `api.deps.get_runtime()` hardcoded `llm=MockLLMClient()` and
`composite_factory=lambda d: CompositeAgent(d, MockLLMClient(), ...)` and never passed
`llm_factory` to `ToolRuntime`. As a result /chat always returned `[mock default]`
even when /onboard/test against the user's real key succeeded.
"""
import pytest
from phd_agent.api import deps
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.profile import UserProfile
from phd_agent.core.composite_agent import CompositeAgent
from phd_agent.core.composite import CompositeToolDefinition
from phd_agent.llm.mock import MockLLMClient
from phd_agent.llm.openai_compat import OpenAICompatClient


@pytest.fixture(autouse=True)
def reset_deps(tmp_path):
    deps._repo = JsonFileRepository(tmp_path)
    deps._runtime = None
    deps.invalidate_profile_cache()
    yield
    deps._repo = None
    deps._runtime = None
    deps.invalidate_profile_cache()


def test_get_runtime_passes_llm_factory_to_tool_runtime():
    runtime = deps.get_runtime()
    assert runtime._llm_factory is deps.get_llm_async, (
        "get_runtime() must wire get_llm_async as ToolRuntime._llm_factory; "
        "otherwise /chat ignores the user's profile."
    )


def test_get_runtime_does_not_hardcode_mock_llm():
    runtime = deps.get_runtime()
    assert not isinstance(runtime.llm, MockLLMClient), (
        "get_runtime() must not bake a MockLLMClient into ToolRuntime.llm; "
        "the per-turn factory is the only source of truth."
    )


@pytest.mark.asyncio
async def test_llm_factory_returns_real_client_when_profile_has_key():
    deps._repo.save_profile_sync = None  # ensure clean fixture (no-op line for clarity)
    repo = deps.get_repo()
    await repo.save_profile(UserProfile(
        llm_provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-realkey1234",
        model_name="gpt-4o-mini",
    ))
    deps.invalidate_profile_cache()
    client, model = await deps.get_llm_async()
    assert isinstance(client, OpenAICompatClient)
    assert model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_llm_factory_falls_back_to_mock_when_no_profile():
    client, model = await deps.get_llm_async()
    assert isinstance(client, MockLLMClient)
    assert model == "mock"


@pytest.mark.asyncio
async def test_composite_factory_uses_user_llm_not_hardcoded_mock():
    repo = deps.get_repo()
    await repo.save_profile(UserProfile(
        llm_provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-realkey1234",
        model_name="gpt-4o-mini",
    ))
    deps.invalidate_profile_cache()
    runtime = deps.get_runtime()

    definition = CompositeToolDefinition(
        tool_id="x", name="x", description="x", system_prompt="x", sub_tools=[],
        owner_user_id="x",
    )
    agent = await runtime._executor._composite_factory(definition)
    assert isinstance(agent, CompositeAgent)
    assert isinstance(agent.llm, OpenAICompatClient), (
        "composite_factory must resolve LLM through get_llm_async, not hardcode MockLLMClient"
    )
    assert agent.model == "gpt-4o-mini", (
        "CompositeAgent must use the model from get_llm_async, not hardcode 'MiniMax-m3'"
    )