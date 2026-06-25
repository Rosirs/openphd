"""In-process async pub/sub for streaming pipeline events to SSE."""
from __future__ import annotations
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class Event:
    run_id: str
    step: int
    agent_id: str
    status: str  # "ok" | "skipped" | "failed" | "end"
    duration_ms: int = 0
    output: dict = field(default_factory=dict)
    error: str | None = None

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Event]]] = defaultdict(list)

    def subscribe(self, run_id: str) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[run_id].append(queue)

        async def gen() -> AsyncIterator[Event]:
            while True:
                yield await queue.get()

        return gen()

    def publish(self, event: Event) -> None:
        for q in self._subscribers.get(event.run_id, []):
            q.put_nowait(event)
