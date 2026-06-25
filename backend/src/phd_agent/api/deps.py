"""Shared dependencies: runtime + repo."""
from __future__ import annotations
import os
from pathlib import Path
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.composite_agent import CompositeAgent

_runtime: ToolRuntime | None = None
_repo: JsonFileRepository | None = None


def _plugins_dir() -> Path:
    return Path(__file__).parent.parent / "plugins"


def _build_llm():
    backend = os.environ.get("LLM_BACKEND", "mock").lower()
    if backend == "openai":
        from phd_agent.llm.openai_compat import OpenAICompatClient
        return OpenAICompatClient(
            base_url=os.environ.get("OPENAI_BASE_URL"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
    from phd_agent.llm.mock import MockLLMClient
    return MockLLMClient()


def get_repo() -> JsonFileRepository:
    global _repo
    if _repo is None:
        _repo = JsonFileRepository(base_dir=os.environ.get("DATA_DIR", "data"))
    return _repo


def get_runtime() -> ToolRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    bus = EventBus()
    registry = AgentRegistry(plugins_dir=_plugins_dir())
    llm = _build_llm()
    wrapper = AgentWrapper(registry, bus, llm)
    repo = get_repo()

    def composite_factory(definition):
        return CompositeAgent(definition, llm, wrapper, bus)

    _runtime = ToolRuntime(
        registry=registry, llm=llm, bus=bus, chat_repo=repo,
        wrapper=wrapper, composite_agent_factory=composite_factory,
        model=os.environ.get("LLM_MODEL", "MiniMax-m3"),
    )
    return _runtime
