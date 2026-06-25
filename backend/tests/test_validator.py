import pytest
from phd_agent.core.contract import AgentContract
from phd_agent.core.validator import validate_pipeline

class _FakeRegistry:
    def __init__(self, contracts: dict[str, AgentContract]) -> None:
        self._c = contracts
    def get_contract(self, agent_id: str) -> AgentContract:
        return self._c[agent_id]

def _c(aid: str, req: set[str], out: set[str]) -> AgentContract:
    return AgentContract(
        agent_id=aid, name=aid, description="d", category="mock",
        required_fields=req, output_fields=out,
    )

def test_happy_path_no_extras():
    reg = _FakeRegistry({
        "a": _c("a", {"x"}, {"y"}),
        "b": _c("b", {"y"}, {"z"}),
    })
    r = validate_pipeline(["a", "b"], reg, bootstrap_fields={"x"})
    assert r.valid is True
    assert r.failed_at is None
    assert all(s.ok for s in r.steps)

def test_missing_field_fails_at_step():
    reg = _FakeRegistry({
        "a": _c("a", {"x"}, {"y"}),
        "b": _c("b", {"not_provided"}, set()),
    })
    r = validate_pipeline(["a", "b"], reg, bootstrap_fields={"x"})
    assert r.valid is False
    assert r.failed_at == 1
    assert r.steps[1].missing == {"not_provided"}

def test_chain_ok_uses_intermediate_outputs():
    reg = _FakeRegistry({
        "intent_parser": _c("intent_parser", {"raw_user_input"}, {"intent"}),
        "mock_echo": _c("mock_echo", {"intent"}, {"dynamic_storage.echo_output"}),
        "mock_logger": _c("mock_echo", {"dynamic_storage.echo_output"}, {"dynamic_storage.run_log"}),
    })
    r = validate_pipeline(["intent_parser", "mock_echo", "mock_logger"], reg)
    # Bootstrap doesn't include raw_user_input → fails at step 0
    assert r.valid is False
    assert r.failed_at == 0

def test_chain_with_bootstrap_ok():
    reg = _FakeRegistry({
        "intent_parser": _c("intent_parser", {"raw_user_input"}, {"intent"}),
        "mock_echo": _c("mock_echo", {"intent"}, {"dynamic_storage.echo_output"}),
        "mock_logger": _c("mock_logger", {"dynamic_storage.echo_output"}, {"dynamic_storage.run_log"}),
    })
    r = validate_pipeline(["intent_parser", "mock_echo", "mock_logger"], reg, bootstrap_fields={"raw_user_input"})
    assert r.valid is True

def test_unknown_agent_raises():
    reg = _FakeRegistry({})
    with pytest.raises(KeyError):
        validate_pipeline(["does_not_exist"], reg)

def test_empty_pipeline_is_valid():
    reg = _FakeRegistry({})
    r = validate_pipeline([], reg)
    assert r.valid is True
    assert r.steps == []