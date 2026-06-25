"""Shared fixtures for council tests."""

from __future__ import annotations

import pytest

from council.providers.base import BaseProvider, Message, ProviderConfig
from council.counselor import Counselor


class MockProvider(BaseProvider):
    """Deterministic provider for testing — echoes a canned response."""

    def __init__(
        self,
        config: ProviderConfig | None = None,
        response: str = "Mock response.",
        fail: bool = False,
    ) -> None:
        cfg = config or ProviderConfig(provider="mock", model="mock-v1")
        super().__init__(cfg)
        self._response = response
        self._fail = fail
        self.call_count = 0
        self.last_messages: list[Message] = []

    async def complete(self, messages: list[Message]) -> str:
        self.call_count += 1
        self.last_messages = messages
        if self._fail:
            raise RuntimeError("Simulated provider failure")
        return self._response


@pytest.fixture
def mock_provider():
    """A working mock provider."""
    return MockProvider(response="I think the answer is 42.")


@pytest.fixture
def failing_provider():
    """A provider that always raises."""
    return MockProvider(response="", fail=True)


@pytest.fixture
def make_counselor():
    """Factory to create counselors with mock providers."""
    def _make(name: str = "TestCounselor", response: str = "Mock.", fail: bool = False):
        provider = MockProvider(response=response, fail=fail)
        return Counselor(name=name, provider=provider)
    return _make
