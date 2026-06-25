"""Composes Validator + Registry + Router + Wrapper + EventBus + Repository."""
from __future__ import annotations
import uuid
from phd_agent.core.events import EventBus, Event
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.repository import IStateRepository, InMemoryRepository
from phd_agent.core.router import CentralRouter
from phd_agent.core.state import GlobalState
from phd_agent.core.validator import validate_pipeline
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.llm.base import BaseLLMClient

class PipelineOrchestrator:
    def __init__(
        self,
        registry: AgentRegistry,
        llm: BaseLLMClient,
        bus: EventBus | None = None,
        repo: IStateRepository | None = None,
    ) -> None:
        self.registry = registry
        self.llm = llm
        self.bus = bus or EventBus()
        self.repo = repo or InMemoryRepository()
        self.router = CentralRouter(registry)
        self.wrapper = AgentWrapper(registry, self.bus, llm)

    async def run(
        self,
        user_id: str,
        active_pipeline: list[str],
        initial_dynamic_storage: dict | None = None,
        user_background: dict | None = None,
    ) -> str:
        # 1. Validate
        ds_keys = {f"dynamic_storage.{k}" for k in dict(initial_dynamic_storage or {}).keys()}
        bootstrap = {"user_id", "user_background", *ds_keys}
        result = validate_pipeline(active_pipeline, self.registry, bootstrap_fields=bootstrap)
        if not result.valid:
            raise ValueError(f"Pipeline invalid at step {result.failed_at}")

        # 2. Init state
        run_id = str(uuid.uuid4())
        state = GlobalState(
            user_id=user_id,
            user_background=user_background or {},
            active_pipeline=list(active_pipeline),
            current_step=0,
            dynamic_storage=dict(initial_dynamic_storage or {}),
            status="running",
        )
        await self.repo.save(user_id, state)

        # 3. Execute loop
        try:
            while True:
                next_id = self.router.dispatch(state)
                if next_id is None:
                    state.status = "completed"
                    break
                await self.wrapper.execute(state, next_id, run_id, self.bus)
                await self.repo.save(user_id, state)
        except Exception:
            state.status = "failed"
            await self.repo.save(user_id, state)
            raise

        if state.error_log:
            state.status = "partial"
        await self.repo.save(user_id, state)

        # 4. End event
        self.bus.publish(Event(
            run_id=run_id, step=state.current_step,
            agent_id="", status="end",
        ))
        return run_id
