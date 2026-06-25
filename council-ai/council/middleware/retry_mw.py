"""Retry middleware — exponential backoff on provider failures."""

from __future__ import annotations

import asyncio
import logging

from ..providers.base import CompletionResult, Message
from . import CompleteFn, Middleware

logger = logging.getLogger("council.middleware.retry")


class RetryMiddleware(Middleware):
    """Retry failed completions with exponential backoff."""

    def __init__(self, max_retries: int = 3, backoff: float = 1.5) -> None:
        self.max_retries = max_retries
        self.backoff = backoff

    def wrap(
        self,
        complete_fn: CompleteFn,
        *,
        counselor_name: str,
        model: str,
        provider_name: str,
        messages: list[Message],
    ) -> CompleteFn:
        async def wrapped() -> CompletionResult:
            delay = 1.0
            last_exc: Exception | None = None
            for attempt in range(self.max_retries + 1):
                try:
                    return await complete_fn()
                except Exception as exc:
                    last_exc = exc
                    if attempt >= self.max_retries:
                        break
                    logger.warning(
                        "Retry %d/%d for %s: %s",
                        attempt + 1,
                        self.max_retries,
                        counselor_name,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    delay *= self.backoff
            raise last_exc  # type: ignore[misc]

        return wrapped
