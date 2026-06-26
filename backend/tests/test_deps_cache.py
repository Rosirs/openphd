import asyncio
import pytest
from phd_agent.api import deps
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.profile import UserProfile
from phd_agent.llm.mock import MockLLMClient
from phd_agent.llm.openai_compat import OpenAICompatClient


@pytest.fixture(autouse=True)
def reset_cache():
    deps.invalidate_profile_cache()
    yield
    deps.invalidate_profile_cache()


def test_get_llm_async_returns_mock_when_no_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(deps, "_repo", JsonFileRepository(tmp_path))
    async def go():
        return await deps.get_llm_async()
    c, m = asyncio.run(go())
    assert isinstance(c, MockLLMClient)
    assert m == "mock"


def test_get_llm_async_uses_profile(tmp_path, monkeypatch):
    repo = JsonFileRepository(tmp_path)
    asyncio.run(repo.save_profile(UserProfile(
        llm_provider="openai",
        base_url="https://api.example.com/v1",
        api_key="sk-test1234",
        model_name="my-model",
    )))
    monkeypatch.setattr(deps, "_repo", repo)

    async def go():
        return await deps.get_llm_async()
    c, m = asyncio.run(go())
    assert isinstance(c, OpenAICompatClient)
    assert c.api_key == "sk-test1234"
    assert c.base_url == "https://api.example.com/v1"
    assert m == "my-model"


def test_invalidate_clears_cache(tmp_path, monkeypatch):
    repo = JsonFileRepository(tmp_path)
    asyncio.run(repo.save_profile(UserProfile(
        llm_provider="openai", base_url="https://x", api_key="first",
        model_name="m1",
    )))
    monkeypatch.setattr(deps, "_repo", repo)

    async def go():
        await deps.get_llm_async()  # prime cache
        deps.invalidate_profile_cache()
        await repo.save_profile(UserProfile(
            llm_provider="openai", base_url="https://y", api_key="second",
            model_name="m2",
        ))
        return await deps.get_llm_async()
    c, m = asyncio.run(go())
    assert c.api_key == "second"
    assert m == "m2"