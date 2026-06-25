"""Mock plugin: echoes dynamic_storage.echo_input."""
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="mock_echo",
    name="Mock Echo",
    description="Echoes dynamic_storage.echo_input into dynamic_storage.echo_output",
    category="mock",
    required_fields={"dynamic_storage.echo_input"},
    output_fields={"dynamic_storage.echo_output"},
    token_budget=0,
)

class MockEchoAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState) -> GlobalState:
        text = state.dynamic_storage.get("echo_input", "")
        state.dynamic_storage["echo_output"] = f"echo: {text}"
        return state
