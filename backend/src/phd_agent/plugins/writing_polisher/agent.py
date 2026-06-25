"""LLM-based writing polisher: improves clarity and tone.

Phase 2: stub — returns input marked as polished.
Phase 3: real LLM call (via ToolRuntime's LLM client).
"""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="writing_polisher",
    name="Writing Polisher",
    description=("Polish a piece of text. "
                 "Args: text (str), style (str, default 'academic')."),
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.polished_text"},
    token_budget=4000,
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to polish"},
            "style": {"type": "string",
                      "enum": ["academic", "casual", "formal", "concise"],
                      "default": "academic"},
        },
        "required": ["text"],
    },
)


class WritingPolisherAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, text: str = "",
                  style: str = "academic") -> GlobalState:
        # Phase 2 stub: prepend style tag. Phase 3 will call LLM.
        state.dynamic_storage["polished_text"] = f"[polished:{style}] {text}"
        return state
