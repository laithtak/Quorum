"""Tests for the Counselor class."""

import pytest

from council.counselor import Counselor
from council.providers.base import Message


@pytest.mark.asyncio
async def test_counselor_responds(make_counselor):
    counselor = make_counselor(name="Alpha", response="The sky is blue.")
    discussion = [Message(role="user", content="What color is the sky?")]
    result = await counselor.respond(discussion)
    assert result == "The sky is blue."


@pytest.mark.asyncio
async def test_counselor_includes_system_prompt(make_counselor):
    counselor = make_counselor(name="Beta", response="ok")
    discussion = [Message(role="user", content="Hello")]
    await counselor.respond(discussion)

    # The provider should have received a system message with the counselor's name
    system_msgs = [m for m in counselor.provider.last_messages if m.role == "system"]
    assert len(system_msgs) == 1
    assert "Beta" in system_msgs[0].content


@pytest.mark.asyncio
async def test_counselor_label(make_counselor):
    counselor = make_counselor(name="Sage")
    assert "Sage" in counselor.label
    assert "mock-v1" in counselor.label


@pytest.mark.asyncio
async def test_counselor_custom_persona():
    from tests.conftest import MockProvider

    provider = MockProvider(response="custom")
    counselor = Counselor(name="X", provider=provider, persona="You are a pirate.")
    assert counselor.persona == "You are a pirate."

    await counselor.respond([Message(role="user", content="Ahoy")])
    system_content = counselor.provider.last_messages[0].content
    assert "pirate" in system_content
