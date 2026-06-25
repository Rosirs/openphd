"""Dispatch atomic vs composite tool execution."""
from __future__ import annotations
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import ToolResult


class ToolExecutor:
    def __init__(self, registry, wrapper, bus, composite_agent_factory=None):
        self._registry = registry
        self._wrapper = wrapper
        self._bus = bus
        self._composite_factory = composite_agent_factory

    async def execute(self, *, name: str, args: dict, state: GlobalState,
                      run_id: str = "ad-hoc") -> ToolResult:
        if self._composite_factory and self._registry.is_composite(name):
            definition = self._registry.get_composite_def(name)
            agent = self._composite_factory(definition)
            return await agent.run(args=args, state=state, run_id=run_id)
        return await self._wrapper.execute_one(state, name, args, run_id=run_id)
