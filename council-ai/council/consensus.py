"""Consensus checking during deliberation."""

from __future__ import annotations

import re

from .counselor import Counselor
from .models import TurnRecord
from .providers.base import Message

CONSENSUS_CHECK_PROMPT = (
    "Has the council reached clear consensus? "
    "Reply YES if they largely agree, or NO if significant disagreement remains."
)


async def check_consensus(
    judge: Counselor,
    discussion: list[Message],
    round_num: int,
) -> tuple[bool, str, TurnRecord]:
    """Ask judge YES/NO; return (agreed, verdict_text, turn_record)."""
    verdict = await judge.respond(
        list(discussion) + [Message(role="user", content=CONSENSUS_CHECK_PROMPT)]
    )
    agreed = bool(re.search(r"\byes\b", verdict, re.IGNORECASE))
    turn = TurnRecord(
        counselor_name=judge.name,
        model=judge.provider.model_name,
        round=round_num,
        content=f"Consensus check: {verdict}",
    )
    return agreed, verdict, turn
