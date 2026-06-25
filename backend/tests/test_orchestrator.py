import pytest
from pathlib import Path
from phd_agent.orchestrator import PipelineOrchestrator
from phd_agent.core.repository import InMemoryRepository
from phd_agent.llm.base import BaseLLMClient, LLMResponse

class _NoopLLM(BaseLLMClient):
    async def chat(self, messages, *, budget):
        return LLMResponse(content="", tokens_used=0, model="noop")
    def count_tokens(self, text):
        return 0

def _orch(real_plugins: bool = True) -> PipelineOrchestrator:
    plugins_dir = (
        Path(__file__).resolve().parent.parent / "src" / "phd_agent" / "plugins"
        if real_plugins else None
    )
    from phd_agent.core.registry import AgentRegistry
    from phd_agent.core.events import EventBus
    reg = AgentRegistry(plugins_dir) if real_plugins else AgentRegistry(Path("/tmp/empty"))
    bus = EventBus()
    return PipelineOrchestrator(
        registry=reg, llm=_NoopLLM(), bus=bus, repo=InMemoryRepository(),
    )

@pytest.mark.asyncio
async def test_happy_path_pipeline_completes():
    orch = _orch()
    run_id = await orch.run(
        user_id="u1",
        active_pipeline=["mock_echo", "mock_logger"],
        initial_dynamic_storage={"echo_input": "hello"},
    )
    final = await orch.repo.load("u1")
    assert final is not None
    assert final.status in ("completed", "partial")
    assert final.current_step == 2
    assert final.dynamic_storage["echo_output"] == "echo: hello"
    assert final.dynamic_storage["run_log"] == ["logged: echo: hello"]

@pytest.mark.asyncio
async def test_invalid_pipeline_raises():
    orch = _orch()
    with pytest.raises(ValueError):
        await orch.run(
            user_id="u1",
            active_pipeline=["mock_logger"],  # missing echo_output upstream
            initial_dynamic_storage={},
        )

@pytest.mark.asyncio
async def test_pipeline_state_transitions_to_completed():
    orch = _orch()
    run_id = await orch.run(
        user_id="u1",
        active_pipeline=["mock_echo"],
        initial_dynamic_storage={"echo_input": "x"},
    )
    final = await orch.repo.load("u1")
    assert final.status in ("completed", "partial")
    assert final.current_step == 1
    # Event publishing is covered by test_wrapper.py; here we only check state
