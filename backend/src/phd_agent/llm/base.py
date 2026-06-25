"""LLM client abstraction."""
from __future__ import annotations
from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict


class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tokens_used: int = 0
    model: str = ""


class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], *, tools: list[dict] | None = None,
                   budget: int = 4000, model: str = "") -> LLMResponse: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
