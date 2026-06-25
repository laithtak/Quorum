"""Logging middleware — records counselor calls and latency."""

from __future__ import annotations

import logging
import time

from ..providers.base import CompletionResult, Message
from . import CompleteFn, Middleware

logger = logging.getLogger("council.middleware.logging")


class LoggingMiddleware(Middleware):
    """Log counselor name, model, and elapsed milliseconds."""

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
            start = time.perf_counter()
            logger.info(
                "Calling %s (%s via %s)", counselor_name, model, provider_name
            )
            result = await complete_fn()
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s completed in %.1f ms", counselor_name, elapsed_ms
            )
            return result

        return wrapped
