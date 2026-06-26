import asyncio
import pytest
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.profile import UserProfile


@pytest.fixture
def repo(tmp_path):
    return JsonFileRepository(tmp_path)


def test_save_and_load_profile(repo):
    p = UserProfile(
        llm_provider="openai", base_url="https://x", api_key="k",
        model_name="gpt-4o-mini",
    )
    asyncio.run(repo.save_profile(p))
    loaded = asyncio.run(repo.load_profile())
    assert loaded is not None
    assert loaded.api_key == "k"


def test_load_profile_missing_returns_none(repo):
    assert asyncio.run(repo.load_profile()) is None


def test_delete_profile(repo):
    p = UserProfile(
        llm_provider="openai", base_url="x", api_key="k", model_name="m",
    )
    asyncio.run(repo.save_profile(p))
    asyncio.run(repo.delete_profile())
    assert asyncio.run(repo.load_profile()) is None