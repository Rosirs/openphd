"""Pluggable state persistence."""
from __future__ import annotations
from abc import ABC, abstractmethod
from phd_agent.core.state import GlobalState

class IStateRepository(ABC):
    @abstractmethod
    async def save(self, user_id: str, state: GlobalState) -> None: ...
    @abstractmethod
    async def load(self, user_id: str) -> GlobalState | None: ...
    @abstractmethod
    async def list_user_pipelines(self, user_id: str) -> list[str]: ...

class InMemoryRepository(IStateRepository):
    """Default impl; lost on process restart."""
    def __init__(self) -> None:
        self._store: dict[str, GlobalState] = {}

    async def save(self, user_id: str, state: GlobalState) -> None:
        self._store[user_id] = state.model_copy(deep=True)

    async def load(self, user_id: str) -> GlobalState | None:
        s = self._store.get(user_id)
        return s.model_copy(deep=True) if s else None

    async def list_user_pipelines(self, user_id: str) -> list[str]:
        """Skeleton: at most one pipeline ('default') per user."""
        return ["default"] if user_id in self._store else []  # per spec §4.2
