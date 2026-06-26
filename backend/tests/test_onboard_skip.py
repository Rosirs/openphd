import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.api import deps
from phd_agent.main import app
from phd_agent.core.json_repo import JsonFileRepository


@pytest.fixture(autouse=True)
def reset_deps_repo():
    deps._repo = None
    deps.invalidate_profile_cache()
    yield
    deps._repo = None
    deps.invalidate_profile_cache()


@pytest.mark.asyncio
async def test_skip_creates_minimal_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/skip")
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        repo = JsonFileRepository(tmp_path)
        profile = await repo.load_profile()
        assert profile is not None
        assert profile.onboarded is True
        assert profile.api_key == ""


@pytest.mark.asyncio
async def test_skip_updates_existing_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/onboard/save", json={
            "llm_provider": "openai", "api_key": "sk-keep-this",
        })
        r = await c.post("/onboard/skip")
        assert r.status_code == 200
        repo = JsonFileRepository(tmp_path)
        profile = await repo.load_profile()
        assert profile.api_key == "sk-keep-this"
        assert profile.onboarded is True