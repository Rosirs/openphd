"""Contract validation: spec §4.1 algorithm. Pure function."""
from __future__ import annotations
from dataclasses import dataclass, field
from phd_agent.core.contract import AgentContract

DEFAULT_BOOTSTRAP = frozenset({"user_id", "user_background"})

@dataclass
class StepValidation:
    step: int
    agent_id: str
    required: set[str]
    provided_at_step: set[str]
    missing: set[str]
    ok: bool

@dataclass
class ValidationResult:
    valid: bool
    failed_at: int | None
    steps: list[StepValidation] = field(default_factory=list)

class _RegistryLike:
    def get_contract(self, agent_id: str) -> AgentContract: ...

def validate_pipeline(
    active_pipeline: list[str],
    registry: _RegistryLike,
    bootstrap_fields: set[str] | None = None,
) -> ValidationResult:
    provided = set(bootstrap_fields) if bootstrap_fields else set(DEFAULT_BOOTSTRAP)
    steps: list[StepValidation] = []

    for idx, agent_id in enumerate(active_pipeline):
        contract = registry.get_contract(agent_id)
        missing = contract.required_fields - provided
        steps.append(StepValidation(
            step=idx,
            agent_id=agent_id,
            required=set(contract.required_fields),
            provided_at_step=set(provided),
            missing=set(missing),
            ok=not missing,
        ))
        if missing:
            return ValidationResult(valid=False, failed_at=idx, steps=steps)
        provided |= contract.output_fields

    return ValidationResult(valid=True, failed_at=None, steps=steps)