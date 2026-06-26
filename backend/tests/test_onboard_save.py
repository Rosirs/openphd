import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.api import deps
from phd_agent.main import app


@pytest.fixture(autouse=True)
def reset_deps_repo():
    deps._repo = None
    deps.invalidate_profile_cache()
    yield
    deps._repo = None
    deps.invalidate_profile_cache()


@pytest.mark.asyncio
async def test_save_persists(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/save", json={
            "llm_provider": "deepseek",
            "api_key": "sk-ds-test1234",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["profile"]["llm_provider"] == "deepseek"
        assert "api.openai.com" not in body["profile"]["base_url"]
        assert (tmp_path / "profile.json").exists()


@pytest.mark.asyncio
async def test_save_rejects_unsupported_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/save", json={
            "llm_provider": "anthropic",
            "api_key": "sk-test",
            "base_url": "https://x",
            "model_name": "claude",
        })
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_save_unknown_provider_400(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/save", json={
            "llm_provider": "notarealprovider",
            "api_key": "sk-test",
        })
        assert r.status_code == 400