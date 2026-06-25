"""Tests for orchestrator memory and usage integration."""

import pytest

from council.memory import ConversationMemory
from council.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_deliberation_with_memory(make_counselor):
    c1 = make_counselor(name="A", response="First answer.")
    memory = ConversationMemory()
    orch = Orchestrator(counselors=[c1], rounds=1, memory=memory)

    await orch.deliberate("Question 1")
    await orch.deliberate("Question 2")

    ctx = memory.get_context()
    assert any("Question 1" in m.content for m in ctx)
    assert any("Question 2" in m.content for m in ctx)


@pytest.mark.asyncio
async def test_deliberation_tracks_usage(make_counselor):
    c1 = make_counselor(name="A", response="Answer.")
    orch = Orchestrator(counselors=[c1], rounds=1)
    result = await orch.deliberate("Usage test")

    assert result.total_cost_usd > 0
    assert len(result.usage) >= 1
