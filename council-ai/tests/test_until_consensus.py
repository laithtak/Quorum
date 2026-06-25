"""Tests for until-consensus deliberation mode."""

from unittest.mock import AsyncMock, patch

import pytest

from council.consensus import check_consensus
from council.models import TurnRecord
from council.orchestrator import Orchestrator


def _consensus_turn(round_num: int, verdict: str, name: str = "Judge") -> TurnRecord:
    return TurnRecord(
        counselor_name=name,
        model="mock-v1",
        round=round_num,
        content=f"Consensus check: {verdict}",
    )


@pytest.mark.asyncio
async def test_stops_early_when_consensus_reached(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(
        counselors=[c1, c2],
        until_consensus=True,
        max_rounds=10,
        synthesizer_index=0,
    )

    with patch(
        "council.orchestrator.check_consensus",
        new_callable=AsyncMock,
        side_effect=[
            (False, "NO", _consensus_turn(1, "NO")),
            (True, "YES", _consensus_turn(2, "YES")),
        ],
    ):
        result = await orch.deliberate("Consensus early stop")

    assert result.rounds_completed == 2
    assert len([t for t in result.turns if t.content.startswith("Consensus check:")]) == 2
    assert result.final_response


@pytest.mark.asyncio
async def test_stops_at_max_rounds_without_consensus(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(
        counselors=[c1, c2],
        until_consensus=True,
        max_rounds=3,
        synthesizer_index=0,
    )

    with patch(
        "council.orchestrator.check_consensus",
        new_callable=AsyncMock,
        return_value=(False, "NO", _consensus_turn(1, "NO")),
    ) as mock_check:
        result = await orch.deliberate("Max rounds cap")

    assert result.rounds_completed == 3
    assert mock_check.call_count == 3
    assert result.final_response


@pytest.mark.asyncio
async def test_fixed_rounds_unchanged(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(counselors=[c1, c2], rounds=3)

    with patch("council.orchestrator.check_consensus", new_callable=AsyncMock) as mock_check:
        result = await orch.deliberate("Fixed rounds")

    mock_check.assert_not_called()
    assert result.rounds_completed == 3
    assert len(result.turns) == 6


@pytest.mark.asyncio
async def test_streaming_yields_consensus_checks(make_counselor):
    c1 = make_counselor(name="A", response="Point A.")
    c2 = make_counselor(name="B", response="Point B.")
    orch = Orchestrator(
        counselors=[c1, c2],
        until_consensus=True,
        max_rounds=5,
        synthesizer_index=0,
    )

    with patch(
        "council.orchestrator.check_consensus",
        new_callable=AsyncMock,
        side_effect=[
            (False, "NO", _consensus_turn(1, "NO")),
            (True, "YES", _consensus_turn(2, "YES")),
        ],
    ):
        items = []
        async for item in orch.deliberate_stream("Stream consensus"):
            items.append(item)

    consensus_items = [
        i
        for i in items
        if isinstance(i, TurnRecord) and i.content.startswith("Consensus check:")
    ]
    assert len(consensus_items) == 2


@pytest.mark.asyncio
async def test_check_consensus_detects_yes(make_counselor):
    judge = make_counselor(name="Judge", response="YES, they agree.")
    agreed, verdict, turn = await check_consensus(judge, [], round_num=1)
    assert agreed is True
    assert "YES" in verdict
    assert turn.content.startswith("Consensus check:")


@pytest.mark.asyncio
async def test_build_from_dict_until_consensus_settings():
    from council.config import build_from_dict

    data = {
        "settings": {
            "until_consensus": True,
            "max_rounds": 12,
            "rounds": 99,
        },
        "counselors": [{"provider": "ollama", "model": "llama3.1"}],
    }
    orch = build_from_dict(data)
    assert orch.until_consensus is True
    assert orch.max_rounds == 12
