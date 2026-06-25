"""Top-level LLM + tool-call loop for chat turns."""
from __future__ import annotations
from typing import AsyncIterator
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.tool_executor import ToolExecutor


SYSTEM_PROMPT = """You are PhD-Agent, an assistant that helps PhD applicants with their application journey.

You can call tools to complete tasks. Before calling a tool, think about what the user needs.
After all work is done, respond clearly and concisely in the same language the user used.
"""


class ToolRuntime:
    def __init__(self, registry: AgentRegistry, llm, bus: EventBus,
                 chat_repo: JsonFileRepository, wrapper: AgentWrapper | None = None,
                 max_tool_calls: int = 10, model: str = "MiniMax-m3",
                 composite_agent_factory=None):
        self.registry = registry
        self.llm = llm
        self.bus = bus
        self.chat_repo = chat_repo
        self.max_tool_calls = max_tool_calls
        self.model = model
        self._wrapper = wrapper or AgentWrapper(registry, bus, llm)
        self._executor = ToolExecutor(registry, self._wrapper, bus, composite_agent_factory)

    async def run_turn(self, session: ChatSession, user_message: str,
                       run_id: str | None = None) -> AsyncIterator[dict]:
        run_id = run_id or f"chat-{session.conversation_id}"
        session.messages.append(Message(role="user", content=user_message))
        yield {"type": "message_received", "run_id": run_id}

        if session.state is None:
            session.state = GlobalState(user_id=session.user_id)

        tool_call_count = 0
        while True:
            tools = await self.registry.list_my_tools(session.user_id)
            response = await self.llm.chat(
                messages=[m.to_llm_dict() for m in self._build_messages(session)],
                tools=tools,
                model=self.model,
            )
            if not response.tool_calls:
                content = response.content or ""
                session.messages.append(Message(role="assistant", content=content))
                session.state.status = "completed"
                await self.chat_repo.save_conversation(session)
                yield {"type": "message_completed", "content": content, "run_id": run_id}
                return

            session.messages.append(Message(
                role="assistant", content=response.content,
                tool_calls=[tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None,
            ))
            exceeded = False
            for tc in response.tool_calls:
                if tool_call_count >= self.max_tool_calls:
                    exceeded = True
                    session.messages.append(Message(
                        role="tool", tool_call_id=tc.id, name=tc.name,
                        content="[skipped: max_tool_calls exceeded]",
                    ))
                    yield {"type": "tool_call_skipped", "name": tc.name, "run_id": run_id}
                    continue
                tool_call_count += 1
                yield {"type": "tool_call_started", "name": tc.name,
                       "args": tc.args, "run_id": run_id}
                result = await self._executor.execute(
                    name=tc.name, args=tc.args, state=session.state, run_id=run_id,
                )
                yield {"type": "tool_call_completed", "name": tc.name,
                       "summary": result.summary, "success": result.success, "run_id": run_id}
                session.messages.append(result.to_message(tc.id))

            await self.chat_repo.save_conversation(session)
            if exceeded:
                yield {"type": "warning",
                       "message": "max_tool_calls exceeded",
                       "run_id": run_id}
            yield {"type": "turn_continued", "run_id": run_id}

    def _build_messages(self, session: ChatSession) -> list[Message]:
        out = [Message(role="system", content=SYSTEM_PROMPT)]
        out.extend(session.messages)
        return out
