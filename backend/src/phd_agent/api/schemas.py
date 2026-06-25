"""Request/response Pydantic models for the HTTP boundary."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class ValidateRequest(BaseModel):
    user_id: str
    active_pipeline: list[str]
    dynamic_storage: dict = Field(default_factory=dict)
    user_background: dict = Field(default_factory=dict)

class StepValidationOut(BaseModel):
    step: int
    agent_id: str
    required: list[str]
    provided_at_step: list[str]
    missing: list[str]
    ok: bool

class ValidateResponse(BaseModel):
    valid: bool
    failed_at: int | None = None
    steps: list[StepValidationOut] = Field(default_factory=list)

class RunRequest(BaseModel):
    user_id: str
    active_pipeline: list[str]
    dynamic_storage: dict = Field(default_factory=dict)
    user_background: dict = Field(default_factory=dict)

class RunResponse(BaseModel):
    run_id: str
    status: Literal["running", "completed", "partial", "failed"]
