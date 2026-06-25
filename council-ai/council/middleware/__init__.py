"""Middleware framework for provider call interception."""

from __future__ import annotations

import abc
from collections.abc import Awaitable, Callable
from typing import Any

from ..providers.base import CompletionResult, Message

CompleteFn = Callable[[], Awaitable[CompletionResult]]


class Middleware(abc.ABC):
    """Base middleware that can wrap provider completion calls."""

    def wrap(
        self,
        complete_fn: CompleteFn,
        *,
        counselor_name: str,
        model: str,
        provider_name: str,
        messages: list[Message],
    ) -> CompleteFn:
        """Return a wrapped completion function."""
        return complete_fn


class MiddlewareStack:
    """Chains middleware around provider completion calls."""

    def __init__(self, middlewares: list[Middleware] | None = None) -> None:
        self.middlewares = middlewares or []

    async def run_complete(
        self,
        complete_fn: CompleteFn,
        *,
        counselor_name: str,
        model: str,
        provider_name: str,
        messages: list[Message],
    ) -> CompletionResult:
        fn = complete_fn
        for mw in reversed(self.middlewares):
            fn = mw.wrap(
                fn,
                counselor_name=counselor_name,
                model=model,
                provider_name=provider_name,
                messages=messages,
            )
        return await fn()

    async def before_deliberation(self, query: str, counselors: list[Any]) -> None:
        for mw in self.middlewares:
            hook = getattr(mw, "before_deliberation", None)
            if hook:
                await hook(query, counselors)

    async def after_deliberation(self, query: str, result: Any) -> None:
        for mw in self.middlewares:
            hook = getattr(mw, "after_deliberation", None)
            if hook:
                await hook(query, result)
