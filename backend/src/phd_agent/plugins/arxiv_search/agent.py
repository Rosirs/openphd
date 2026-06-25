"""ArXiv search plugin: returns a list of paper dicts."""
from __future__ import annotations
import httpx
import xml.etree.ElementTree as ET
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="arxiv_search",
    name="ArXiv Search",
    description="Search arXiv for papers. Args: query (str), max_results (int, default 5).",
    category="academic",
    required_fields=set(),
    output_fields={"dynamic_storage.arxiv_results"},
    token_budget=0,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
        },
        "required": ["query"],
    },
)

NS = {"a": "http://www.w3.org/2005/Atom"}


class ArxivSearchAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, query: str = "",
                  max_results: int = 5) -> GlobalState:
        url = (
            "http://export.arxiv.org/api/query"
            f"?search_query=all:{query}&max_results={max_results}"
        )
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(url)
                r.raise_for_status()
                root = ET.fromstring(r.text)
        except Exception as e:
            state.error_log.append({"agent_id": self.contract.agent_id,
                                     "error": f"arxiv fetch failed: {e}"})
            state.dynamic_storage["arxiv_results"] = []
            return state
        results = []
        for entry in root.findall("a:entry", NS):
            title = (entry.findtext("a:title", default="", namespaces=NS) or "").strip()
            summary = (entry.findtext("a:summary", default="", namespaces=NS) or "").strip()
            link = entry.find("a:link[@rel='alternate']", NS)
            url_v = link.get("href") if link is not None else ""
            authors = [
                (a.findtext("a:name", default="", namespaces=NS) or "").strip()
                for a in entry.findall("a:author", NS)
            ]
            results.append({
                "title": title,
                "summary": summary,
                "url": url_v,
                "authors": authors,
            })
        state.dynamic_storage["arxiv_results"] = results
        return state
