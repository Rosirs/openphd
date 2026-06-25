"""Central dispatcher: reads state.current_step, returns next agent_id or None=END."""
from __future__ import annotations
from phd_agent.core.state import GlobalState

class CentralRouter:
    def __init__(self, registry) -> None:
        self._registry = registry  # held for future validation hooks

    def dispatch(self, state: GlobalState) -> str | None:
        if state.current_step >= len(state.active_pipeline):
            return None
        return state.active_pipeline[state.current_step]