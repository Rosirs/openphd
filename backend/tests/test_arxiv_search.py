"""Test arxiv_search plugin with mocked HTTP."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from phd_agent.plugins.arxiv_search.agent import ArxivSearchAgent
from phd_agent.core.state import GlobalState


def test_arxiv_search_writes_results():
    fake_xml = """<?xml version='1.0'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <title>Test Paper</title>
    <summary>An abstract.</summary>
    <link rel='alternate' href='http://arxiv.org/abs/123'/>
    <author><name>Alice</name></author>
  </entry>
</feed>"""
    fake_response = AsyncMock(text=fake_xml)
    fake_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=fake_response)):
        agent = ArxivSearchAgent()
        state = GlobalState(user_id="u1")
        asyncio.run(agent.run(state, query="ML", max_results=1))
        results = state.dynamic_storage["arxiv_results"]
        assert len(results) == 1
        assert results[0]["title"] == "Test Paper"
        assert results[0]["authors"] == ["Alice"]


def test_arxiv_search_handles_failure():
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=Exception("net err"))):
        agent = ArxivSearchAgent()
        state = GlobalState(user_id="u1")
        asyncio.run(agent.run(state, query="ML"))
        assert state.dynamic_storage["arxiv_results"] == []
        assert any("arxiv" in e.get("error", "") for e in state.error_log)
