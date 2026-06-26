"""Shared dependencies: runtime + repo + profile cache."""
from __future__ import annotations
import os
from pathlib import Path
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.composite_agent import CompositeAgent
from phd_agent.llm.base import BaseLLMClient
from phd_agent.llm.mock import MockLLMClient
from phd_agent.llm.openai_compat import OpenAICompatClient

_runtime: ToolRuntime | None = None
_repo: JsonFileRepository | None = None
_llm_client: BaseLLMClient | None = None
_llm_model: str = "mock"


def _plugins_dir() -> Path:
    return Path(__file__).parent.parent / "plugins"


def get_repo() -> JsonFileRepository:
    global _repo
    if _repo is None:
        _repo = JsonFileRepository(base_dir=os.environ.get("DATA_DIR", "data"))
    return _repo


async def get_llm_async() -> tuple[BaseLLMClient, str]:
    """Return (client, model_name). Uses cached values; falls back to MockLLMClient."""
    global _llm_client, _llm_model
    if _llm_client is not None:
        return _llm_client, _llm_model
    profile = await get_repo().load_profile()
    if profile and profile.api_key:
        _llm_client = OpenAICompatClient(
            base_url=profile.base_url, api_key=profile.api_key,
        )
        _llm_model = profile.model_name
    else:
        _llm_client = MockLLMClient()
        _llm_model = "mock"
    return _llm_client, _llm_model


def invalidate_profile_cache() -> None:
    """Drop cached client (called after /onboard/save)."""
    global _llm_client, _llm_model
    _llm_client = None
    _llm_model = "mock"


def get_runtime() -> ToolRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    bus = EventBus()
    registry = AgentRegistry(plugins_dir=_plugins_dir())
    wrapper = AgentWrapper(registry, bus, llm=None)
    repo = get_repo()

    def composite_factory(definition):
        from phd_agent.llm.mock import MockLLMClient
        return CompositeAgent(definition, MockLLMClient(), wrapper, bus)

    _runtime = ToolRuntime(
        registry=registry, llm=MockLLMClient(), bus=bus, chat_repo=repo,
        wrapper=wrapper, composite_agent_factory=composite_factory,
        model="mock",  # overridden per-turn via get_llm_async
    )
    return _runtime