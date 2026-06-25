"""Mock plugin: logs dynamic_storage.echo_output into dynamic_storage.run_log."""
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="mock_logger",
    name="Mock Logger",
    description="Appends dynamic_storage.echo_output to dynamic_storage.run_log",
    category="mock",
    required_fields={"dynamic_storage.echo_output"},
    output_fields={"dynamic_storage.run_log"},
    token_budget=0,
)

class MockLoggerAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState) -> GlobalState:
        echo = state.dynamic_storage.get("echo_output", "")
        log = state.dynamic_storage.get("run_log", [])
        log.append(f"logged: {echo}")
        state.dynamic_storage["run_log"] = log
        return state
