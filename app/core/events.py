import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AdminEvent:
    event: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def serialize(self) -> str:
        return json.dumps(asdict(self))


class AdminEventBus:
    """In-process pub/sub for admin dashboard live updates."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    async def publish(self, event: str, data: dict[str, Any]) -> None:
        payload = AdminEvent(event=event, data=data).serialize()
        async with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                continue


admin_event_bus = AdminEventBus()
