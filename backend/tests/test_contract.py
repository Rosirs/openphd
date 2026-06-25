from phd_agent.core.contract import AgentContract, BaseAgent
from phd_agent.core.state import GlobalState
import pytest

def test_agent_contract_minimal_valid():
    c = AgentContract(
        agent_id="mock_echo",
        name="Mock Echo",
        description="echoes input",
        category="mock",
        required_fields={"dynamic_storage.echo_input"},
        output_fields={"dynamic_storage.echo_output"},
    )
    assert c.agent_id == "mock_echo"
    assert c.token_budget == 4000  # default from spec
    assert c.isolation == "in_process"  # default

def test_agent_contract_serializes_to_json():
    c = AgentContract(
        agent_id="x", name="X", description="d", category="mock",
        required_fields={"a"}, output_fields={"b"},
    )
    j = c.model_dump_json()
    restored = AgentContract.model_validate_json(j)
    assert restored.agent_id == "x"

def test_base_agent_subclass_must_declare_contract():
    class Bad(BaseAgent):
        async def run(self, state):
            return state
    with pytest.raises(TypeError):
        Bad()  # contract is required

def test_base_agent_subclass_runs():
    class Echo(BaseAgent):
        contract = AgentContract(
            agent_id="e", name="E", description="d", category="mock",
            required_fields=set(), output_fields=set(),
        )
        async def run(self, state: GlobalState) -> GlobalState:
            state.dynamic_storage["ok"] = True
            return state
    a = Echo()
    state = GlobalState(user_id="u1")
    import asyncio
    asyncio.run(a.run(state))
    assert state.dynamic_storage["ok"] is True
