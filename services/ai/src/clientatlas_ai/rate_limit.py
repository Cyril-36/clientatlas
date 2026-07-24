from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from uuid import UUID

from clientatlas_ai.errors import SafeServiceError


class SlidingWindowRateLimiter:
    def __init__(self, *, limit: int, window_seconds: float) -> None:
        self._limit = limit
        self._window = window_seconds
        self._events: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, user_id: UUID, operation: str) -> None:
        key = f"{user_id}:{operation}"
        now = time.monotonic()
        cutoff = now - self._window
        async with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self._limit:
                raise SafeServiceError("rate_limit_exceeded", status_code=429)
            events.append(now)


expensive_operation_limiter = SlidingWindowRateLimiter(
    limit=10,
    window_seconds=60,
)
