"""Per-agent token budget enforcement (spec §6)."""
from __future__ import annotations

class TokenGuardrail:
    def __init__(self, llm) -> None:
        self._llm = llm

    def truncate_to_budget(self, text: str, budget: int) -> str:
        if budget <= 0:
            return ""
        tokens = self._llm.count_tokens(text)
        if tokens <= budget:
            return text
        # Approximate: 4 chars per token; preserve head (more important than tail)
        char_budget = budget * 4
        return text[:char_budget]
