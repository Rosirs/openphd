"""API integration tests (Phase 2)."""
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_BACKEND", "mock")
    yield


@pytest.mark.asyncio
async def test_health(env):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
        assert r.status_code == 200
        assert r.json() == {"ok": True}


@pytest.mark.asyncio
async def test_tools_catalog(env):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/tools/catalog", params={"user_id": "u1"})
        assert r.status_code == 200
        tools = r.json()["tools"]
        ids = {t["name"] for t in tools}
        assert "arxiv_search" in ids
        assert "knowledge_retriever" in ids
        assert "writing_polisher" in ids
        assert "email_drafter" in ids
        assert "pdf_summarizer" in ids
        assert "mock_echo" in ids
        assert "mock_logger" in ids


@pytest.mark.asyncio
async def test_create_and_list_conversations(env):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/chat/conversations", json={"user_id": "u1", "title": "t"})
        assert r.status_code == 200
        cid = r.json()["conversation_id"]
        r = await c.get("/chat/conversations", params={"user_id": "u1"})
        assert r.status_code == 200
        assert any(x["conversation_id"] == cid for x in r.json()["conversations"])


@pytest.mark.asyncio
async def test_canvas_preview_and_save(env):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/canvas/preview-prompt", json={
            "name": "T", "system_prompt": "summarize", "sub_tools": ["arxiv_search"],
        })
        assert r.status_code == 200
        assert "summarize" in r.json()["augmented_system_prompt"]
        r = await c.post("/canvas/composite?user_id=u1", json={
            "tool_id": "t1", "name": "T", "description": "d",
            "system_prompt": "summarize", "sub_tools": ["arxiv_search"],
        })
        assert r.status_code == 200
        r = await c.get("/tools/catalog", params={"user_id": "u1"})
        ids = {t["name"] for t in r.json()["tools"]}
        assert "t1" in ids


@pytest.mark.asyncio
async def test_chat_message_stream(env):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/chat/conversations", json={"user_id": "u1"})
        cid = r.json()["conversation_id"]
        r = await c.post(f"/chat/conversations/{cid}/messages?user_id=u1",
                         json={"content": "hi"})
        assert r.status_code == 200
        body = r.text
        assert "message_received" in body
        assert "message_completed" in body
