"""File-system backed repository for chat sessions and composite tools."""
from __future__ import annotations
from pathlib import Path
from phd_agent.core.chat import ChatSession
from phd_agent.core.composite import CompositeToolDefinition


class JsonFileRepository:
    def __init__(self, base_dir):
        self.base = Path(base_dir)

    def _conv_path(self, user_id: str, conv_id: str) -> Path:
        return self.base / user_id / "conversations" / f"{conv_id}.json"

    def _tool_path(self, user_id: str, tool_id: str) -> Path:
        return self.base / user_id / "composite_tools" / f"{tool_id}.json"

    async def save_conversation(self, session: ChatSession) -> None:
        p = self._conv_path(session.user_id, session.conversation_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(session.model_dump_json(indent=2))

    async def load_conversation(self, user_id: str, conv_id: str) -> ChatSession | None:
        p = self._conv_path(user_id, conv_id)
        if not p.exists():
            return None
        return ChatSession.model_validate_json(p.read_text())

    async def list_conversations(self, user_id: str) -> list[ChatSession]:
        d = self.base / user_id / "conversations"
        if not d.exists():
            return []
        out: list[ChatSession] = []
        for f in d.glob("*.json"):
            try:
                out.append(ChatSession.model_validate_json(f.read_text()))
            except Exception:
                continue
        return out

    async def delete_conversation(self, user_id: str, conv_id: str) -> None:
        p = self._conv_path(user_id, conv_id)
        if p.exists():
            p.unlink()

    async def save_composite_tool(self, tool: CompositeToolDefinition) -> None:
        p = self._tool_path(tool.owner_user_id, tool.tool_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(tool.model_dump_json(indent=2))

    async def load_composite_tool(self, user_id: str, tool_id: str) -> CompositeToolDefinition | None:
        p = self._tool_path(user_id, tool_id)
        if not p.exists():
            return None
        return CompositeToolDefinition.model_validate_json(p.read_text())

    async def list_composite_tools(self, user_id: str) -> list[CompositeToolDefinition]:
        d = self.base / user_id / "composite_tools"
        if not d.exists():
            return []
        out: list[CompositeToolDefinition] = []
        for f in d.glob("*.json"):
            try:
                out.append(CompositeToolDefinition.model_validate_json(f.read_text()))
            except Exception:
                continue
        return out

    async def delete_composite_tool(self, user_id: str, tool_id: str) -> None:
        p = self._tool_path(user_id, tool_id)
        if p.exists():
            p.unlink()
