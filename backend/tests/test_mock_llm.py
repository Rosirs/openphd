"""Tests for MockLLMClient."""
import pytest
from phd_agent.llm.mock import MockLLMClient


def test_mock_returns_text_response():
    import asyncio
    llm = MockLLMClient(responses=["hello world"])
    r = asyncio.run(llm.chat(messages=[{"role": "user", "content": "hi"}], tools=[]))
    assert r.content == "hello world"
    assert r.tool_calls is None


def test_mock_returns_tool_call():
    import asyncio
    llm = MockLLMClient(responses=[None], tool_calls=[
        {"id": "tc1", "name": "t1", "args": {"x": 1}}
    ])
    r = asyncio.run(llm.chat(messages=[{"role": "user", "content": "hi"}], tools=[{"name": "t1"}]))
    assert r.content is None
    assert r.tool_calls[0].name == "t1"
    assert r.tool_calls[0].args == {"x": 1}
