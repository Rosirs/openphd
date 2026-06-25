"""Agent contract declaration (input/output schema + metadata)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import ClassVar, Literal
from pydantic import BaseModel

Category = Literal["academic", "writing", "admin", "mock"]
Isolation = Literal["in_process"]

class AgentContract(BaseModel):
    agent_id: str
    name: str
    description: str
    category: Category
    required_fields: set[str]
    output_fields: set[str]
    token_budget: int = 4000
    isolation: Isolation = "in_process"

class BaseAgent(ABC):
    """Abstract base class all plugins must subclass."""
    contract: ClassVar[AgentContract]

    def __init__(self):
        if "contract" not in type(self).__dict__:
            raise TypeError(f"{type(self).__name__} must declare a `contract` ClassVar")

    @abstractmethod
    async def run(self, state) -> object:
        """Execute business logic; do not catch your own exceptions."""
