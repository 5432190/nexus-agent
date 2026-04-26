"""Token bucket rate limiter for Nexus Agent."""

from __future__ import annotations

import asyncio
import time
from typing import Optional


class TokenBucket:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_time = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_time
        self._last_time = now
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

    async def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> None:
        if tokens > self._capacity:
            raise ValueError("Requested tokens exceed bucket capacity")

        deadline = None if timeout is None else time.monotonic() + timeout
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                if deadline is not None and time.monotonic() >= deadline:
                    raise asyncio.TimeoutError("Rate limiter acquire timed out")

                sleep_time = (tokens - self._tokens) / self._rate
                await asyncio.sleep(max(sleep_time, 0.01))
