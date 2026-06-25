"""Tests for chat data models."""
from datetime import datetime
from phd_agent.core.chat import Message, ChatSession, ToolCall
from phd_agent.core.state import GlobalState


def test_message_serialization():
    msg = Message(role="user", content="hello", timestamp=datetime(2026, 6, 25, 12, 0))
    data = msg.model_dump_json()
    msg2 = Message.model_validate_json(data)
    assert msg2 == msg


def test_message_to_llm_dict():
    msg = Message(
        role="assistant", content="hi", timestamp=datetime.now(),
        tool_calls=[ToolCall(id="tc1", name="t1", args={"x": 1})],
    )
    d = msg.to_llm_dict()
    assert d["role"] == "assistant"
    assert d["content"] == "hi"
    assert d["tool_calls"][0]["name"] == "t1"
    assert "timestamp" not in d


def test_chat_session_with_messages():
    s = ChatSession(
        user_id="u1", conversation_id="c1", title="test",
        messages=[Message(role="user", content="hi")],
        state=GlobalState(user_id="u1"),
    )
    assert s.user_id == "u1"
    assert len(s.messages) == 1
    assert s.state.user_id == "u1"
