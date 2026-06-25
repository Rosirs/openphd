"""Knowledge retriever: dispatches to configured backend (default: arxiv)."""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState
from phd_agent.plugins.arxiv_search.agent import ArxivSearchAgent

CONTRACT = AgentContract(
    agent_id="knowledge_retriever",
    name="Knowledge Retriever",
    description=("Retrieve knowledge from a backend. "
                 "Args: query (str), backend (str, default 'arxiv'), "
                 "max_results (int, default 5)."),
    category="academic",
    required_fields=set(),
    output_fields={"dynamic_storage.retrieved"},
    token_budget=0,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "backend": {"type": "string", "enum": ["arxiv"], "default": "arxiv"},
            "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
    },
)

_BACKENDS = {"arxiv": ArxivSearchAgent()}


class KnowledgeRetrieverAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, query: str = "",
                  backend: str = "arxiv", max_results: int = 5) -> GlobalState:
        agent = _BACKENDS.get(backend)
        if agent is None:
            state.error_log.append({
                "agent_id": self.contract.agent_id,
                "error": f"unknown backend: {backend}",
            })
            state.dynamic_storage["retrieved"] = []
            return state
        await agent.run(state, query=query, max_results=max_results)
        state.dynamic_storage["retrieved"] = state.dynamic_storage.get("arxiv_results", [])
        return state
