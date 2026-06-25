import json
import sys
from pathlib import Path
import pytest
from phd_agent.core.registry import AgentRegistry

def _write_plugin(parent: Path, agent_id: str, contract: dict, agent_code: str) -> None:
    p = parent / agent_id
    p.mkdir()
    (p / "contract.json").write_text(json.dumps(contract))
    (p / "__init__.py").write_text("")
    (p / "agent.py").write_text(agent_code)

@pytest.fixture
def plugins_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _write_plugin(
        tmp_path, "echo_test",
        {"agent_id": "echo_test", "name": "Echo Test", "description": "d",
         "category": "mock", "required_fields": [], "output_fields": []},
        "from phd_agent.plugins._base import BaseAgent\n"
        "from phd_agent.core.contract import AgentContract\n"
        "from phd_agent.core.state import GlobalState\n"
        "CONTRACT = AgentContract(agent_id='echo_test', name='Echo Test', description='d', category='mock', required_fields=set(), output_fields=set())\n"
        "class EchoTestAgent(BaseAgent):\n"
        "    contract = CONTRACT\n"
        "    async def run(self, state: GlobalState) -> GlobalState:\n"
        "        state.dynamic_storage['marker'] = 'echo_test_ran'\n"
        "        return state\n",
    )
    # Make the fake plugin importable as phd_agent.plugins.echo_test by
    # aliasing tmp_path onto the existing phd_agent.plugins package.
    import phd_agent.plugins as _plugins_pkg
    _plugins_pkg.__path__.append(str(tmp_path))  # type: ignore[attr-defined]
    monkeypatch.delitem(sys.modules, "phd_agent.plugins.echo_test", raising=False)
    yield tmp_path
    if str(tmp_path) in _plugins_pkg.__path__:  # type: ignore[attr-defined]
        _plugins_pkg.__path__.remove(str(tmp_path))  # type: ignore[attr-defined]

def test_scan_finds_contracts(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    c = reg.get_contract("echo_test")
    assert c.agent_id == "echo_test"

def test_list_agent_ids(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    assert reg.list_agent_ids() == ["echo_test"]

def test_unknown_agent_raises_keyerror(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    with pytest.raises(KeyError):
        reg.get_contract("ghost")

def test_lazy_load_creates_instance(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    agent = reg.load("echo_test")
    assert agent.contract.agent_id == "echo_test"

@pytest.mark.asyncio
async def test_loaded_agent_can_execute(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    from phd_agent.core.state import GlobalState
    agent = reg.load("echo_test")
    state = GlobalState(user_id="u1")
    await agent.run(state)
    assert state.dynamic_storage["marker"] == "echo_test_ran"
