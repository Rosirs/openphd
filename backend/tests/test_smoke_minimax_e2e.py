"""End-to-end smoke test: /chat routes through the user's MiniMax profile, not MockLLMClient.

Background: pre-fix, /chat always returned `[mock default]` because deps.get_runtime()
hardcoded `llm=MockLLMClient()` and never read the saved profile. This test exercises
the full HTTP stack (FastAPI ASGI + httpx ASGITransport) and proves the post-fix wiring
reaches OpenAICompatClient when a MiniMax profile is saved.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app
from phd_agent.api import deps
from phd_agent.llm.mock import MockLLMClient


def _mock_async_client(post_return_value=None):
    """Build a mock httpx.AsyncClient that supports async context manager."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=post_return_value)
    mock_class = MagicMock()
    mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_class.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_class, mock_client


def _parse_sse_events(text: str) -> list[dict]:
    """Parse SSE stream into list of event dicts."""
    events: list[dict] = []
    for block in text.split("\n\n"):
        ev_type = None
        data_line = None
        for line in block.splitlines():
            if line.startswith("event: "):
                ev_type = line[len("event: "):]
            elif line.startswith("data: "):
                data_line = line[len("data: "):]
        if ev_type and data_line:
            events.append({"event": ev_type, "data": json.loads(data_line)})
    return events


@pytest.fixture(autouse=True)
def reset_deps(tmp_path, monkeypatch):
    """Reset all global dep state so each test is isolated."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    deps._repo = None
    deps._runtime = None
    deps.invalidate_profile_cache()
    yield
    deps._repo = None
    deps._runtime = None
    deps.invalidate_profile_cache()


@pytest.mark.asyncio
async def test_chat_uses_minimax_profile_not_mock():
    """Full HTTP stack: save MiniMax profile, post chat message, verify response
    came from OpenAICompatClient (not MockLLMClient)."""
    # 1. Monkey-patch httpx.AsyncClient in openai_compat to return canned MiniMax response
    fake_response = AsyncMock()
    fake_response.json = lambda: {
        "choices": [{"message": {"content": "hello from MiniMax", "tool_calls": None}}],
        "usage": {"total_tokens": 7},
    }
    fake_response.raise_for_status = lambda: None
    mock_class, mock_client = _mock_async_client(post_return_value=fake_response)

    with patch("phd_agent.llm.openai_compat.httpx.AsyncClient", mock_class):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            # 2. Save MiniMax profile
            r = await c.post("/onboard/save", json={
                "llm_provider": "MiniMax",
                "base_url": "https://api.MiniMax.chat/v1",
                "model_name": "MiniMax-M3",
                "api_key": "sk-fakekey",
            })
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["profile"]["llm_provider"] == "MiniMax"
            assert body["profile"]["model_name"] == "MiniMax-M3"

            # Drop cached client AND runtime so /chat rebuilds with new profile
            deps.invalidate_profile_cache()
            deps._runtime = None

            # 3. Create a conversation
            r = await c.post("/chat/conversations", json={"user_id": "u1"})
            assert r.status_code == 200, r.text
            cid = r.json()["conversation_id"]

            # 4. Post a chat message; collect SSE stream
            r = await c.post(
                f"/chat/conversations/{cid}/messages?user_id=u1",
                json={"content": "hi"},
            )
            assert r.status_code == 200, r.text

            events = _parse_sse_events(r.text)
            assert any(e["event"] == "message_received" for e in events), (
                f"expected message_received in events, got: {events}"
            )

            completed = [e for e in events if e["event"] == "message_completed"]
            assert len(completed) == 1, (
                f"expected exactly one message_completed event, got: {events}"
            )
            assert completed[0]["data"]["content"] == "hello from MiniMax", (
                "message_completed content must come from the canned OpenAICompatClient "
                "response — if it is '[mock default]', the runtime is still hardcoding MockLLMClient"
            )

            # 5. Verify the patched httpx was actually invoked (proving OpenAICompatClient was hit)
            assert mock_client.post.await_count == 1, (
                "OpenAICompatClient.post should have been called exactly once"
            )
            call_args = mock_client.post.await_args
            called_url = call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
            assert called_url == "https://api.MiniMax.chat/v1/chat/completions", (
                f"expected OpenAICompatClient to POST to MiniMax endpoint, got: {called_url!r}"
            )

            # 6. The deps-cached LLM client must be OpenAICompatClient, not MockLLMClient.
            # If it were MockLLMClient, its .chat() would have produced `[mock default]`,
            # not the canned "hello from MiniMax" we asserted above.
            assert not isinstance(deps._llm_client, MockLLMClient), (
                f"deps._llm_client must be OpenAICompatClient after saving a MiniMax profile, "
                f"got {type(deps._llm_client).__name__}"
            )
