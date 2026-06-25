"""Composite tool: LLM-driven nested agent definition."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

SYSTEM_PROMPT_TEMPLATE = """You are {name}.

{user_intent}

You can call the following sub-tools to complete your task:
{tool_list}

Behavior:
- After receiving the task, autonomously decide which sub-tools to call and in what order.
- Sub-tool results are fed back to you; decide the next step based on the result.
- After completing all work, return a concise final result (do not repeat intermediate steps).
- Maximum {max_sub_iterations} sub-tool calls.
"""


def build_system_prompt(*, name: str, user_intent: str, sub_tools: list[str],
                        max_sub_iterations: int) -> str:
    tool_list = "\n".join(f"- {t}" for t in sub_tools)
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=name,
        user_intent=user_intent,
        tool_list=tool_list,
        max_sub_iterations=max_sub_iterations,
    )


class CompositeToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    system_prompt: str
    sub_tools: list[str]
    owner_user_id: str
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
