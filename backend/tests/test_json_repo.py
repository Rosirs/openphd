"""Tests for JsonFileRepository."""
import pytest
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.composite import CompositeToolDefinition


@pytest.fixture
def tmp_repo(tmp_path):
    return JsonFileRepository(tmp_path)


def test_save_and_load_conversation(tmp_repo):
    import asyncio
    s = ChatSession(user_id="u1", conversation_id="c1", title="t",
                    messages=[Message(role="user", content="hi")])
    asyncio.run(tmp_repo.save_conversation(s))
    loaded = asyncio.run(tmp_repo.load_conversation("u1", "c1"))
    assert loaded is not None
    assert loaded.messages[0].content == "hi"


def test_list_conversations(tmp_repo):
    import asyncio
    for cid in ["c1", "c2"]:
        asyncio.run(tmp_repo.save_conversation(ChatSession(user_id="u1", conversation_id=cid, title=cid)))
    convs = asyncio.run(tmp_repo.list_conversations("u1"))
    assert {c.conversation_id for c in convs} == {"c1", "c2"}


def test_save_and_list_composite_tool(tmp_repo):
    import asyncio
    t = CompositeToolDefinition(tool_id="t1", name="T", description="d",
                                 system_prompt="p", sub_tools=["a"], owner_user_id="u1")
    asyncio.run(tmp_repo.save_composite_tool(t))
    loaded = asyncio.run(tmp_repo.load_composite_tool("u1", "t1"))
    assert loaded.tool_id == "t1"
    tools = asyncio.run(tmp_repo.list_composite_tools("u1"))
    assert len(tools) == 1


def test_delete_conversation(tmp_repo):
    import asyncio
    s = ChatSession(user_id="u1", conversation_id="c1", title="t")
    asyncio.run(tmp_repo.save_conversation(s))
    asyncio.run(tmp_repo.delete_conversation("u1", "c1"))
    assert asyncio.run(tmp_repo.load_conversation("u1", "c1")) is None
