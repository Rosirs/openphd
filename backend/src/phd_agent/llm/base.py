"""LLM client abstraction (spec §4.2)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    tokens_used: int
    model: str

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], *, budget: int) -> LLMResponse: ...
    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
