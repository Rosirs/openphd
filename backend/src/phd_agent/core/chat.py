"""Chat session data models: Message + ChatSession."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from phd_agent.core.state import GlobalState


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_llm_dict(self) -> dict:
        """Serialize for LLM API (drops timestamp)."""
        d: dict = {"role": self.role}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = [t.model_dump() for t in self.tool_calls]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


class ChatSession(BaseModel):
    user_id: str
    conversation_id: str
    title: str = ""
    messages: list[Message] = Field(default_factory=list)
    state: GlobalState | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Literal["active", "archived"] = "active"
