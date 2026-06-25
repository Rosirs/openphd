"""Deterministic LLM for tests + dev-without-API-key."""
from __future__ import annotations
from phd_agent.llm.base import BaseLLMClient, LLMResponse, ToolCall


class MockLLMClient(BaseLLMClient):
    def __init__(self, responses: list[str | None] | None = None,
                 tool_calls: list[dict] | None = None):
        self.responses = list(responses or ["[mock response]"])
        self.tool_calls = list(tool_calls or [])
        self.call_count = 0

    async def chat(self, messages, *, tools=None, budget=4000, model="mock"):
        self.call_count += 1
        if self.tool_calls:
            tc_dict = self.tool_calls.pop(0)
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(**tc_dict)],
                tokens_used=10,
                model=model,
            )
        text = self.responses.pop(0) if self.responses else "[mock default]"
        return LLMResponse(content=text, tool_calls=None, tokens_used=10, model=model)

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
