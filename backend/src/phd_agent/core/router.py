"""Central dispatcher: reads state.current_step, returns next agent_id or None=END."""
from __future__ import annotations
from phd_agent.core.state import GlobalState

class CentralRouter:
    def __init__(self, registry) -> None:
        # Reserved for future per-pipeline validation hooks; not currently consulted.
        self._registry = registry

    def dispatch(self, state: GlobalState) -> str | None:
        if state.current_step >= len(state.active_pipeline):
            return None
        return state.active_pipeline[state.current_step]