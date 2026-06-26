"""User LLM profile stored in data/profile.json."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    llm_provider: str
    base_url: str
    api_key: str
    model_name: str
    onboarded: bool = False
    onboarded_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.now)

    def masked_key(self) -> str:
        """Mask API key for display: 'sk-...xxxx' (first 3 + last 4)."""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:3]}...{self.api_key[-4:]}"