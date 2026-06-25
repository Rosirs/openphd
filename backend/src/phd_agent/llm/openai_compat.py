"""OpenAI-compatible LLM client (supports tool calling)."""
from __future__ import annotations
import json
import os
import httpx
from phd_agent.llm.base import BaseLLMClient, LLMResponse, ToolCall


class OpenAICompatClient(BaseLLMClient):
    def __init__(self, base_url: str | None = None,
                 api_key: str | None = None,
                 timeout: float = 60.0):
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL")
                         or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

    async def chat(self, messages, *, tools=None, budget=4000, model=""):
        model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        body: dict = {"model": model, "messages": messages}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(
                f"{self.base_url}/chat/completions",
                json=body, headers=headers,
            )
            r.raise_for_status()
            data = r.json()
        msg = data["choices"][0]["message"]
        tool_calls: list[ToolCall] | None = None
        if msg.get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    args=json.loads(tc["function"]["arguments"]),
                )
                for tc in msg["tool_calls"]
            ]
        return LLMResponse(
            content=msg.get("content"),
            tool_calls=tool_calls,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=model,
        )

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
