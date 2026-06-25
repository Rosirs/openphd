"""Sandboxed agent execution: try/except isolation, step increment, event publish."""
from __future__ import annotations
import time
from phd_agent.core.contract import BaseAgent
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState

class AgentWrapper:
    def __init__(self, registry, bus, llm) -> None:
        self._registry = registry
        # bus and llm are reserved for future use:
        # - bus: per-call bus override for testability (currently passed in execute())
        # - llm: per-agent LLM invocation in agent.run
        self._bus = bus
        self._llm = llm

    async def execute(self, state: GlobalState, agent_id: str, run_id: str, bus: EventBus) -> None:
        from phd_agent.core.events import Event  # local import to avoid cycle in test
        started = time.perf_counter()
        status = "ok"
        error_msg: str | None = None
        try:
            agent: BaseAgent = self._registry.load(agent_id)
            await agent.run(state)
        except Exception as e:
            status = "skipped"
            error_msg = f"{type(e).__name__}: {e}"
            state.error_log.append({
                "step": state.current_step,
                "agent_id": agent_id,
                "error": error_msg,
            })
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            state.current_step += 1
            bus.publish(Event(
                run_id=run_id,
                step=state.current_step - 1,
                agent_id=agent_id,
                status=status,
                duration_ms=duration_ms,
                error=error_msg,
            ))
