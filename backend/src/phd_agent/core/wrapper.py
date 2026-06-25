"""Sandboxed agent execution: try/except isolation, event publish."""
from __future__ import annotations
import time
from pydantic import BaseModel, Field
from phd_agent.core.contract import BaseAgent
from phd_agent.core.events import EventBus, Event
from phd_agent.core.state import GlobalState


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    summary: str
    state_delta: dict = Field(default_factory=dict)
    llm_context: str
    error: str | None = None

    def to_message(self, tool_call_id: str):
        from phd_agent.core.chat import Message  # local to avoid cycle
        return Message(
            role="tool",
            tool_call_id=tool_call_id,
            name=self.tool_name,
            content=self.llm_context,
        )


class AgentWrapper:
    def __init__(self, registry, bus, llm):
        self._registry = registry
        self._bus = bus
        self._llm = llm

    async def execute_one(self, state: GlobalState, name: str, args: dict,
                          run_id: str = "ad-hoc") -> ToolResult:
        """Execute one atomic agent with explicit args. No current_step increment."""
        started = time.perf_counter()
        error_msg: str | None = None
        try:
            agent: BaseAgent = self._registry.load(name)
            await agent.run(state, **args)
        except TypeError as e:
            # likely bad args — surface clearly
            error_msg = f"bad args for {name}: {e}"
            state.error_log.append({"agent_id": name, "error": error_msg})
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            state.error_log.append({"agent_id": name, "error": error_msg})
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._bus.publish(Event(
                run_id=run_id, step=0, agent_id=name,
                status="ok" if not error_msg else "skipped",
                duration_ms=duration_ms, error=error_msg,
            ))
        if error_msg:
            return ToolResult(
                tool_name=name, success=False, summary=f"failed: {error_msg}",
                llm_context=f"[tool {name} failed: {error_msg}]",
                error=error_msg,
            )
        return ToolResult(
            tool_name=name, success=True, summary="ok",
            llm_context=f"[tool {name} completed]",
        )

    async def execute(self, state: GlobalState, agent_id: str, run_id: str,
                      bus: EventBus) -> None:
        """Legacy execute with current_step increment (composite-internal use)."""
        await self.execute_one(state, agent_id, args={}, run_id=run_id)
        if state.current_step < len(state.active_pipeline):
            state.current_step += 1
