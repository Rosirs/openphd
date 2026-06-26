from datetime import datetime
from phd_agent.core.profile import UserProfile


def test_profile_roundtrip():
    p = UserProfile(
        llm_provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-abc123456789",
        model_name="gpt-4o-mini",
    )
    data = p.model_dump_json()
    p2 = UserProfile.model_validate_json(data)
    assert p2.llm_provider == "openai"
    assert p2.api_key == "sk-abc123456789"


def test_masked_key_normal():
    p = UserProfile(
        llm_provider="openai", base_url="x", api_key="sk-abc123456789",
        model_name="gpt-4o-mini",
    )
    assert p.masked_key() == "sk-...6789"


def test_masked_key_short():
    p = UserProfile(
        llm_provider="openai", base_url="x", api_key="short",
        model_name="gpt-4o-mini",
    )
    assert p.masked_key() == "***"


def test_masked_key_empty():
    p = UserProfile(
        llm_provider="openai", base_url="x", api_key="",
        model_name="gpt-4o-mini",
    )
    assert p.masked_key() == ""


def test_profile_defaults():
    p = UserProfile(
        llm_provider="openai", base_url="x", api_key="k", model_name="m",
    )
    assert p.onboarded is False
    assert p.onboarded_at is None
    assert isinstance(p.updated_at, datetime)