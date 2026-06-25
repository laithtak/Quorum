"""Tests for the Orchestrator."""

import pytest

from council.orchestrator import Orchestrator, TurnRecord


@pytest.mark.asyncio
async def test_basic_deliberation(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(counselors=[c1, c2], rounds=1)

    result = await orch.deliberate("Test query")

    assert result.query == "Test query"
    assert result.rounds_completed == 1
    assert len(result.turns) == 2
    assert result.turns[0].counselor_name == "A"
    assert result.turns[1].counselor_name == "B"
    assert result.final_response  # synthesis produced something


@pytest.mark.asyncio
async def test_multiple_rounds(make_counselor):
    c1 = make_counselor(name="A", response="Round response.")
    c2 = make_counselor(name="B", response="Round response.")
    orch = Orchestrator(counselors=[c1, c2], rounds=3)

    result = await orch.deliberate("Multi-round test")

    assert result.rounds_completed == 3
    # 2 counselors × 3 rounds = 6 turns
    assert len(result.turns) == 6


@pytest.mark.asyncio
async def test_parallel_mode(make_counselor):
    c1 = make_counselor(name="P1", response="Parallel 1.")
    c2 = make_counselor(name="P2", response="Parallel 2.")
    orch = Orchestrator(counselors=[c1, c2], rounds=1, parallel_within_round=True)

    result = await orch.deliberate("Parallel test")

    assert len(result.turns) == 2
    assert result.final_response


@pytest.mark.asyncio
async def test_single_counselor(make_counselor):
    c = make_counselor(name="Solo", response="Only me.")
    orch = Orchestrator(counselors=[c], rounds=2)

    result = await orch.deliberate("Solo test")

    assert result.rounds_completed == 2
    assert len(result.turns) == 2  # 1 counselor × 2 rounds


@pytest.mark.asyncio
async def test_counselor_failure_is_handled(make_counselor):
    good = make_counselor(name="Good", response="I'm fine.")
    bad = make_counselor(name="Bad", fail=True)
    orch = Orchestrator(counselors=[good, bad], rounds=1)

    result = await orch.deliberate("Failure test")

    assert len(result.turns) == 2
    assert "unable to respond" in result.turns[1].content


@pytest.mark.asyncio
async def test_parallel_failure_handled(make_counselor):
    good = make_counselor(name="Good", response="OK.")
    bad = make_counselor(name="Bad", fail=True)
    orch = Orchestrator(counselors=[good, bad], rounds=1, parallel_within_round=True)

    result = await orch.deliberate("Parallel failure test")

    assert len(result.turns) == 2
    assert "unable to respond" in result.turns[1].content


@pytest.mark.asyncio
async def test_streaming(make_counselor):
    c1 = make_counselor(name="S1", response="Stream 1.")
    c2 = make_counselor(name="S2", response="Stream 2.")
    orch = Orchestrator(counselors=[c1, c2], rounds=1)

    items = []
    async for item in orch.deliberate_stream("Stream test"):
        items.append(item)

    # 2 TurnRecords + 1 final string
    turn_records = [i for i in items if isinstance(i, TurnRecord)]
    finals = [i for i in items if isinstance(i, str)]
    assert len(turn_records) == 2
    assert len(finals) == 1


@pytest.mark.asyncio
async def test_transcript_format(make_counselor):
    c1 = make_counselor(name="A", response="Hello.")
    orch = Orchestrator(counselors=[c1], rounds=1)

    result = await orch.deliberate("Transcript test")

    transcript = result.transcript
    assert "Query: Transcript test" in transcript
    assert "Round 1" in transcript
    assert "Final Response" in transcript


def test_no_counselors_raises():
    with pytest.raises(ValueError, match="at least one"):
        Orchestrator(counselors=[], rounds=1)


def test_zero_rounds_raises(make_counselor):
    c = make_counselor()
    with pytest.raises(ValueError, match="at least 1"):
        Orchestrator(counselors=[c], rounds=0)
