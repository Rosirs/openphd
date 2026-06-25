"""Global state shared across all agents in a pipeline run."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["idle", "running", "partial", "completed", "failed"]

class GlobalState(BaseModel):
    user_id: str
    user_background: dict = Field(default_factory=dict)
    active_pipeline: list[str] = Field(default_factory=list)
    current_step: int = 0
    dynamic_storage: dict = Field(default_factory=dict)
    error_log: list[dict] = Field(default_factory=list)
    status: Status = "idle"
