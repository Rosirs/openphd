import pytest
from phd_agent.core.repository import InMemoryRepository
from phd_agent.core.state import GlobalState

@pytest.mark.asyncio
async def test_save_and_load_round_trip():
    repo = InMemoryRepository()
    s = GlobalState(user_id="u1", active_pipeline=["a", "b"])
    await repo.save("u1", s)
    loaded = await repo.load("u1")
    assert loaded is not None
    assert loaded.active_pipeline == ["a", "b"]

@pytest.mark.asyncio
async def test_load_missing_user_returns_none():
    repo = InMemoryRepository()
    assert await repo.load("ghost") is None

@pytest.mark.asyncio
async def test_save_overwrites():
    repo = InMemoryRepository()
    await repo.save("u1", GlobalState(user_id="u1", active_pipeline=["a"]))
    await repo.save("u1", GlobalState(user_id="u1", active_pipeline=["a", "b"]))
    loaded = await repo.load("u1")
    assert loaded.active_pipeline == ["a", "b"]

@pytest.mark.asyncio
async def test_list_user_pipelines_returns_ids_for_user():
    repo = InMemoryRepository()
    await repo.save("u1", GlobalState(user_id="u1"))
    assert await repo.list_user_pipelines("u1") == ["default"]
    assert await repo.list_user_pipelines("ghost") == []  # per-user, per spec §4.2
