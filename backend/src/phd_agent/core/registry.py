"""Discovers plugin contracts at startup; lazy-loads plugin classes on demand."""
from __future__ import annotations
import importlib
from inspect import isclass
from pathlib import Path
from phd_agent.core.contract import AgentContract, BaseAgent


class AgentRegistry:
    def __init__(self, plugins_dir: Path | None = None) -> None:
        self._dir = plugins_dir
        self._contracts: dict[str, AgentContract] = {}
        self._classes: dict[str, type[BaseAgent]] = {}
        self._composite_defs: dict[str, object] = {}  # tool_id -> CompositeToolDefinition
        if plugins_dir is not None:
            self._scan()

    def _scan(self) -> None:
        if self._dir is None or not self._dir.exists():
            return
        for plugin_dir in self._dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue
            contract_file = plugin_dir / "contract.json"
            if not contract_file.exists():
                continue
            contract = AgentContract.model_validate_json(contract_file.read_text())
            self._contracts[contract.agent_id] = contract

    def register(self, contract: AgentContract, cls: type[BaseAgent]) -> None:
        """Manually register a plugin (used when contract.json is not present, e.g. tests)."""
        self._contracts[contract.agent_id] = contract
        self._classes[contract.agent_id] = cls

    def list_agent_ids(self) -> list[str]:
        return sorted(self._contracts.keys())

    def get_contract(self, agent_id: str) -> AgentContract:
        return self._contracts[agent_id]

    def load(self, agent_id: str) -> BaseAgent:
        if agent_id not in self._classes:
            module = importlib.import_module(f"phd_agent.plugins.{agent_id}.agent")
            cls = next(
                v for v in vars(module).values()
                if isclass(v) and issubclass(v, BaseAgent) and v is not BaseAgent
            )
            self._classes[agent_id] = cls
        return self._classes[agent_id]()

    def load_composites(self, composite_list) -> None:
        """Register a list of CompositeToolDefinition objects."""
        self._composite_defs = {t.tool_id: t for t in composite_list}

    def is_composite(self, name: str) -> bool:
        return name in self._composite_defs

    def get_composite_def(self, name: str):
        return self._composite_defs[name]

    def _contract_to_spec(self, contract: AgentContract) -> dict:
        return {
            "name": contract.agent_id,
            "description": contract.description,
            "parameters": contract.parameters,
            "category": contract.category,
        }

    def _composite_to_spec(self, definition) -> dict:
        return {
            "name": definition.tool_id,
            "description": definition.description,
            "parameters": {"type": "object", "properties": {}},
            "category": "composite",
        }

    async def list_my_tools(self, user_id: str) -> list[dict]:
        """All tools visible to this user (atomic + composite)."""
        atomic = [self._contract_to_spec(c) for c in self._contracts.values()]
        composite = [self._composite_to_spec(t) for t in self._composite_defs.values()]
        return atomic + composite
