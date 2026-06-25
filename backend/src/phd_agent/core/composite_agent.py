"""LLM-driven nested agent: executes a composite tool via its own LLM loop."""
from __future__ import annotations
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt
from phd_agent.core.wrapper import AgentWrapper, ToolResult
from phd_agent.core.state import GlobalState
from phd_agent.core.chat import Message
from phd_agent.core.events import EventBus, Event
from phd_agent.core.contract import AgentContract

MAX_SUB_ITERATIONS = 5


class CompositeAgent:
    def __init__(self, definition: CompositeToolDefinition, llm, wrapper: AgentWrapper,
                 bus: EventBus, max_sub_iterations: int = MAX_SUB_ITERATIONS):
        self.definition = definition
        self.llm = llm
        self.wrapper = wrapper
        self.bus = bus
        self.max_sub_iterations = max_sub_iterations

    async def run(self, *, args: dict, state: GlobalState,
                  run_id: str = "composite") -> ToolResult:
        sub_messages: list[Message] = [
            Message(role="system", content=self._build_prompt()),
            Message(role="user", content=f"任务输入: {args}"),
        ]
        sub_tools = [self._contract_to_spec(self.wrapper._registry.get_contract(t))
                     for t in self.definition.sub_tools]

        for i in range(self.max_sub_iterations):
            self.bus.publish(Event(run_id=run_id, step=i,
                                   agent_id=self.definition.tool_id,
                                   status="sub_iter", duration_ms=0))
            response = await self.llm.chat(
                messages=[m.to_llm_dict() for m in sub_messages],
                tools=sub_tools,
                model="MiniMax-m3",
            )
            if not response.tool_calls:
                content = response.content or ""
                return ToolResult(
                    tool_name=self.definition.tool_id, success=True,
                    summary=content[:200],
                    llm_context=content,
                )
            sub_messages.append(Message(
                role="assistant", content=response.content,
                tool_calls=[tc.model_dump() for tc in response.tool_calls],
            ))
            for tc in response.tool_calls:
                self.bus.publish(Event(run_id=run_id, step=i, agent_id=tc.name,
                                       status="sub_call", duration_ms=0))
                # sub-execution only allowed for atomic tools
                if self.wrapper._registry.is_composite(tc.name):
                    err = f"composite cannot call composite: {tc.name}"
                    sub_messages.append(Message(
                        role="tool", tool_call_id=tc.id, name=tc.name,
                        content=f"[error: {err}]",
                    ))
                    continue
                sub_result = await self.wrapper.execute_one(state, tc.name, tc.args,
                                                            run_id=run_id)
                self.bus.publish(Event(run_id=run_id, step=i, agent_id=tc.name,
                                       status="sub_call_done", duration_ms=0))
                sub_messages.append(sub_result.to_message(tc.id))

        return ToolResult(
            tool_name=self.definition.tool_id, success=False,
            summary=f"sub iteration limit {self.max_sub_iterations} reached",
            llm_context="[sub-agent failed: iteration limit]",
            error="max_sub_iterations",
        )

    def _build_prompt(self) -> str:
        return build_system_prompt(
            name=self.definition.name,
            user_intent=self.definition.system_prompt,
            sub_tools=self.definition.sub_tools,
            max_sub_iterations=self.max_sub_iterations,
        )

    def _contract_to_spec(self, contract: AgentContract) -> dict:
        return {
            "name": contract.agent_id,
            "description": contract.description,
            "parameters": contract.parameters,
        }
