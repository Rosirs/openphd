import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


def _mock_async_client(post_return_value=None, post_side_effect=None):
    """Build a mock httpx.AsyncClient that supports async context manager."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=post_return_value,
                                  side_effect=post_side_effect)
    # Make the class itself an async context manager
    mock_class = MagicMock()
    mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_class.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_class, mock_client


@pytest.mark.asyncio
async def test_test_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    fake_response = AsyncMock()
    fake_response.json = lambda: {
        "choices": [{"message": {"content": "pong", "tool_calls": None}}],
        "usage": {"total_tokens": 5},
    }
    fake_response.raise_for_status = lambda: None
    mock_class, _ = _mock_async_client(post_return_value=fake_response)
    with patch("phd_agent.llm.openai_compat.httpx.AsyncClient", mock_class):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/onboard/test", json={
                "llm_provider": "openai",
                "api_key": "sk-test",
                "base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4o-mini",
            })
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["ok"] is True
            assert body["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_test_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    mock_class, _ = _mock_async_client(post_side_effect=Exception("401 unauthorized"))
    with patch("phd_agent.llm.openai_compat.httpx.AsyncClient", mock_class):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/onboard/test", json={
                "llm_provider": "openai",
                "api_key": "sk-bad",
            })
            assert r.status_code == 200
            body = r.json()
            assert body["ok"] is False
            assert "401" in body["message"] or "unauthorized" in body["message"].lower()


@pytest.mark.asyncio
async def test_test_rejects_anthropic(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/test", json={
            "llm_provider": "anthropic",
            "api_key": "sk-test",
        })
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_test_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/onboard/test", json={
            "llm_provider": "openai",
            "api_key": "",
        })
        assert r.status_code == 400