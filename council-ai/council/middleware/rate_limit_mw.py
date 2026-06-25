"""Rate limit middleware — token bucket per provider."""

from __future__ import annotations

import asyncio
import time

from ..providers.base import CompletionResult, Message
from . import CompleteFn, Middleware


class _TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


class RateLimitMiddleware(Middleware):
    """Token-bucket rate limiter keyed on provider name."""

    def __init__(self, rate: float = 10.0, capacity: float = 10.0) -> None:
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, _TokenBucket] = {}

    def _bucket_for(self, provider_name: str) -> _TokenBucket:
        if provider_name not in self._buckets:
            self._buckets[provider_name] = _TokenBucket(self.rate, self.capacity)
        return self._buckets[provider_name]

    def wrap(
        self,
        complete_fn: CompleteFn,
        *,
        counselor_name: str,
        model: str,
        provider_name: str,
        messages: list[Message],
    ) -> CompleteFn:
        bucket = self._bucket_for(provider_name)

        async def wrapped() -> CompletionResult:
            await bucket.acquire()
            return await complete_fn()

        return wrapped
