import asyncio
import pytest
from phd_agent.core.events import EventBus, Event

@pytest.mark.asyncio
async def test_subscriber_receives_published_events():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-1", step=0, agent_id="a", status="ok", duration_ms=10))
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "a"
    assert event.status == "ok"

@pytest.mark.asyncio
async def test_subscriber_does_not_receive_other_run_events():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-2", step=0, agent_id="a", status="ok", duration_ms=10))
    bus.publish(Event(run_id="run-1", step=0, agent_id="b", status="ok", duration_ms=10))
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "b"

@pytest.mark.asyncio
async def test_multiple_subscribers_to_same_run():
    bus = EventBus()
    s1 = bus.subscribe("run-1")
    s2 = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-1", step=0, agent_id="a", status="ok", duration_ms=10))
    e1 = await asyncio.wait_for(s1.__anext__(), timeout=0.5)
    e2 = await asyncio.wait_for(s2.__anext__(), timeout=0.5)
    assert e1.agent_id == "a"
    assert e2.agent_id == "a"
