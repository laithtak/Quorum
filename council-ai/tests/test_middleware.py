"""Tests for middleware stack."""

import logging

import pytest

from council.middleware import MiddlewareStack
from council.middleware.cache_mw import CacheMiddleware
from council.middleware.logging_mw import LoggingMiddleware
from council.middleware.retry_mw import RetryMiddleware
from council.providers.base import Message
from tests.conftest import MockProvider
from council.counselor import Counselor
from council.middleware import Middleware


class FlakyMiddleware(Middleware):
    """Test helper that counts calls."""

    def __init__(self):
        self.before_count = 0

    def wrap(self, complete_fn, **kwargs):
        async def wrapped():
            self.before_count += 1
            return await complete_fn()
        return wrapped


@pytest.mark.asyncio
async def test_retry_on_failure():
    provider = MockProvider(fail=True)
    counselor = Counselor(name="Retry", provider=provider)
    stack = MiddlewareStack([RetryMiddleware(max_retries=2, backoff=0.01)])
    counselor.middleware = stack

    with pytest.raises(RuntimeError):
        await counselor.respond([Message(role="user", content="test")])

    assert provider.call_count == 3


@pytest.mark.asyncio
async def test_cache_hit_skips_duplicate_calls():
    provider = MockProvider(response="cached")
    counselor = Counselor(name="Cache", provider=provider)
    stack = MiddlewareStack([CacheMiddleware(backend="memory")])
    counselor.middleware = stack
    messages = [Message(role="user", content="same question")]

    r1 = await counselor.respond(messages)
    r2 = await counselor.respond(messages)
    assert r1 == r2
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_logging_emits(caplog):
    provider = MockProvider(response="logged")
    counselor = Counselor(name="LogTest", provider=provider)
    stack = MiddlewareStack([LoggingMiddleware()])
    counselor.middleware = stack

    with caplog.at_level(logging.INFO, logger="council.middleware.logging"):
        await counselor.respond([Message(role="user", content="hi")])

    assert any("LogTest" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_middleware_stack_chains():
    provider = MockProvider(response="ok")
    counselor = Counselor(name="Chain", provider=provider)
    flaky = FlakyMiddleware()
    stack = MiddlewareStack([flaky, CacheMiddleware()])
    counselor.middleware = stack
    await counselor.respond([Message(role="user", content="x")])
    assert flaky.before_count == 1
