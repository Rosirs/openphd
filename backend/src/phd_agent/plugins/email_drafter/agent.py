"""LLM-based email drafter for PhD outreach.

Phase 2: stub — returns a templated draft. Phase 3: real LLM call.
"""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="email_drafter",
    name="Email Drafter",
    description=("Draft an email. "
                 "Args: purpose (str), context (str), target (str, default 'advisor')."),
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.email_draft"},
    token_budget=4000,
    parameters={
        "type": "object",
        "properties": {
            "purpose": {"type": "string", "description": "Email purpose"},
            "context": {"type": "string", "description": "Background context"},
            "target": {"type": "string",
                       "enum": ["advisor", "lab", "department", "collaborator"],
                       "default": "advisor"},
        },
        "required": ["purpose"],
    },
)


class EmailDrafterAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, purpose: str = "",
                  context: str = "", target: str = "advisor") -> GlobalState:
        state.dynamic_storage["email_draft"] = (
            f"Subject: {purpose}\n\n"
            f"Dear Professor,\n\n{context}\n\nBest regards"
        )
        return state
