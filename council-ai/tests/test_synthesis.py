"""Tests for synthesis strategies."""

import pytest

from council.orchestrator import Orchestrator
from council.synthesis import (
    SingleSynthesizer,
    VotingSynthesizer,
    ConsensusChecker,
    RankedSynthesizer,
)


@pytest.mark.asyncio
async def test_single_synthesizer(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(
        counselors=[c1, c2],
        rounds=1,
        synthesis_engine=SingleSynthesizer(),
    )
    result = await orch.deliberate("Test")
    assert result.final_response


@pytest.mark.asyncio
async def test_voting_synthesizer_extra_turns(make_counselor):
    c1 = make_counselor(name="Alpha", response="Alpha wins.")
    c2 = make_counselor(name="Beta", response="Beta idea.")
    c3 = make_counselor(name="Gamma", response="I vote Alpha.")
    orch = Orchestrator(
        counselors=[c1, c2, c3],
        rounds=1,
        synthesis_engine=VotingSynthesizer(),
    )
    result = await orch.deliberate("Vote test")
    assert result.final_response
    assert len(result.turns) >= 3


@pytest.mark.asyncio
async def test_consensus_checker(make_counselor):
    c1 = make_counselor(name="Judge", response="YES we agree.")
    c2 = make_counselor(name="A", response="Agreed.")
    orch = Orchestrator(
        counselors=[c1, c2],
        rounds=1,
        synthesis_engine=ConsensusChecker(synthesizer_index=0),
    )
    result = await orch.deliberate("Consensus?")
    assert result.final_response
    assert any("Consensus check" in t.content for t in result.turns)


@pytest.mark.asyncio
async def test_ranked_synthesizer(make_counselor):
    c1 = make_counselor(name="First", response="Best answer.")
    c2 = make_counselor(name="Second", response="Second answer.")
    c3 = make_counselor(name="Ranker", response="First, Second")
    orch = Orchestrator(
        counselors=[c1, c2, c3],
        rounds=1,
        synthesis_engine=RankedSynthesizer(),
    )
    result = await orch.deliberate("Rank test")
    assert result.final_response


@pytest.mark.asyncio
async def test_default_single_matches_v01(make_counselor):
    c1 = make_counselor(name="A", response="Legacy.")
    orch = Orchestrator(counselors=[c1], rounds=1)
    result = await orch.deliberate("Legacy test")
    assert result.final_response == "Legacy."
