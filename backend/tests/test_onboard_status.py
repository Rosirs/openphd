import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.mark.asyncio
async def test_status_initial(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/onboard/status")
        assert r.status_code == 200
        body = r.json()
        assert body["configured"] is False
        assert body["onboarded"] is False
        assert body["profile"] is None
        assert any(p["key"] == "openai" for p in body["providers"])


@pytest.mark.asyncio
async def test_status_after_save_masks_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/onboard/save", json={
            "llm_provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-secret1234abcd",
            "model_name": "gpt-4o-mini",
        })
        r = await c.get("/onboard/status")
        body = r.json()
        assert body["configured"] is True
        assert body["onboarded"] is True
        assert "sk-secret1234abcd" not in str(body)
        assert "sk-...abcd" in body["profile"]["api_key_masked"]


@pytest.mark.asyncio
async def test_status_anthropic_listed_as_unsupported(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/onboard/status")
        providers = {p["key"]: p for p in r.json()["providers"]}
        assert providers["anthropic"]["supported"] is False
        assert providers["openai"]["supported"] is True