"""LLM-based text/PDF summarizer.

Phase 2: stub. Phase 3: real LLM call.
"""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="pdf_summarizer",
    name="Text/PDF Summarizer",
    description=("Summarize a piece of text. "
                 "Args: text (str), focus (str, default '')."),
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.summary"},
    token_budget=4000,
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to summarize"},
            "focus": {"type": "string", "default": ""},
        },
        "required": ["text"],
    },
)


class PdfSummarizerAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, text: str = "",
                  focus: str = "") -> GlobalState:
        # Phase 2 stub: take first 200 chars
        preview = text[:200] if text else ""
        state.dynamic_storage["summary"] = f"[summary focus={focus}] {preview}..."
        return state
