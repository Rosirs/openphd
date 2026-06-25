"""Discovers plugin contracts at startup; lazy-loads plugin classes on demand."""
from __future__ import annotations
import importlib
import json
from inspect import isclass
from pathlib import Path
from phd_agent.core.contract import AgentContract, BaseAgent

class AgentRegistry:
    def __init__(self, plugins_dir: Path) -> None:
        self._dir = plugins_dir
        self._contracts: dict[str, AgentContract] = {}
        self._classes: dict[str, type[BaseAgent]] = {}
        self._scan()

    def _scan(self) -> None:
        for plugin_dir in self._dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue
            contract_file = plugin_dir / "contract.json"
            if not contract_file.exists():
                continue
            contract = AgentContract.model_validate_json(contract_file.read_text())
            self._contracts[contract.agent_id] = contract

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
