"""Synthesis engines — strategies for producing the final council response."""

from __future__ import annotations

import abc
from collections import Counter
from dataclasses import dataclass

from .consensus import check_consensus
from .counselor import Counselor
from .models import TurnRecord
from .providers.base import Message

SYNTHESIS_PROMPT = (
    "The council has finished deliberating. "
    "Synthesize the discussion into a single, clear, final response for the user. "
    "Incorporate the strongest points from all counselors. "
    "Resolve any disagreements by choosing the best-supported position. "
    "Do NOT mention the council, the deliberation process, or individual counselors — "
    "respond as if you are giving the user a direct answer."
)


class SynthesisEngine(abc.ABC):
    """Abstract synthesis strategy."""

    @abc.abstractmethod
    async def synthesize(
        self,
        counselors: list[Counselor],
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> tuple[str, list[TurnRecord]]:
        """Return final response and any extra turns from synthesis."""
        ...


@dataclass
class SingleSynthesizer(SynthesisEngine):
    """Designated counselor synthesizes the final answer (default)."""

    synthesizer_index: int = 0

    async def synthesize(
        self,
        counselors: list[Counselor],
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> tuple[str, list[TurnRecord]]:
        synthesizer = counselors[self.synthesizer_index % len(counselors)]
        synthesis_messages = list(discussion) + [
            Message(role="user", content=SYNTHESIS_PROMPT)
        ]
        final = await synthesizer.respond(synthesis_messages)
        return final, []


@dataclass
class VotingSynthesizer(SynthesisEngine):
    """Counselors vote on last-round responses; majority wins."""

    synthesizer_index: int = 0

    async def synthesize(
        self,
        counselors: list[Counselor],
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> tuple[str, list[TurnRecord]]:
        if not turns:
            return "", []

        last_round = max(t.round for t in turns)
        candidates = [t for t in turns if t.round == last_round]
        if len(candidates) <= 1:
            synth = SingleSynthesizer(self.synthesizer_index)
            return await synth.synthesize(counselors, discussion, turns)

        vote_prompt = (
            "The council has finished deliberating. Review the last-round responses "
            "and reply with ONLY the name of the counselor whose answer is strongest. "
            f"Candidates: {', '.join(t.counselor_name for t in candidates)}"
        )
        votes: list[str] = []
        extra_turns: list[TurnRecord] = []
        for counselor in counselors:
            response = await counselor.respond(
                list(discussion) + [Message(role="user", content=vote_prompt)]
            )
            extra_turns.append(
                TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=last_round + 1,
                    content=f"Vote: {response}",
                )
            )
            for c in candidates:
                if c.counselor_name.lower() in response.lower():
                    votes.append(c.counselor_name)
                    break

        if votes:
            winner = Counter(votes).most_common(1)[0][0]
            for c in candidates:
                if c.counselor_name == winner:
                    return c.content, extra_turns

        synth = SingleSynthesizer(self.synthesizer_index)
        final, synth_extra = await synth.synthesize(counselors, discussion, turns)
        return final, extra_turns + synth_extra


@dataclass
class ConsensusChecker(SynthesisEngine):
    """Check for consensus; if none, run an extra round then synthesize."""

    synthesizer_index: int = 0

    async def synthesize(
        self,
        counselors: list[Counselor],
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> tuple[str, list[TurnRecord]]:
        judge = counselors[self.synthesizer_index % len(counselors)]
        check_round = (max(t.round for t in turns) if turns else 0) + 1
        agreed, _verdict, consensus_turn = await check_consensus(
            judge, discussion, check_round
        )
        extra_turns: list[TurnRecord] = [consensus_turn]

        if agreed:
            last_round = max(t.round for t in turns) if turns else 0
            last_responses = [t for t in turns if t.round == last_round]
            if last_responses:
                combined = "\n\n".join(
                    f"[{t.counselor_name}]: {t.content}" for t in last_responses
                )
                return combined, extra_turns

        extra_discussion = list(discussion)
        bonus_round = (max(t.round for t in turns) if turns else 0) + 1
        for counselor in counselors:
            response = await counselor.respond(extra_discussion)
            extra_turns.append(
                TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=bonus_round,
                    content=response,
                )
            )
            extra_discussion.append(
                Message(role="assistant", content=f"[{counselor.name}]: {response}")
            )

        synth = SingleSynthesizer(self.synthesizer_index)
        final, synth_extra = await synth.synthesize(counselors, extra_discussion, turns)
        return final, extra_turns + synth_extra


@dataclass
class RankedSynthesizer(SynthesisEngine):
    """Borda-count ranking of last-round responses."""

    synthesizer_index: int = 0

    async def synthesize(
        self,
        counselors: list[Counselor],
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> tuple[str, list[TurnRecord]]:
        if not turns:
            return "", []

        last_round = max(t.round for t in turns)
        candidates = [t for t in turns if t.round == last_round]
        if len(candidates) <= 1:
            synth = SingleSynthesizer(self.synthesizer_index)
            return await synth.synthesize(counselors, discussion, turns)

        names = [c.counselor_name for c in candidates]
        rank_prompt = (
            "Rank the following counselor responses from best to worst. "
            f"Reply with counselor names only, comma-separated: {', '.join(names)}"
        )
        scores: Counter[str] = Counter()
        extra_turns: list[TurnRecord] = []
        n = len(candidates)
        for counselor in counselors:
            response = await counselor.respond(
                list(discussion) + [Message(role="user", content=rank_prompt)]
            )
            extra_turns.append(
                TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=last_round + 1,
                    content=f"Ranking: {response}",
                )
            )
            ranked = [s.strip() for s in response.split(",")]
            for i, name in enumerate(ranked):
                for c in candidates:
                    if c.counselor_name.lower() in name.lower():
                        scores[c.counselor_name] += n - i
                        break

        if scores:
            winner = scores.most_common(1)[0][0]
            for c in candidates:
                if c.counselor_name == winner:
                    return c.content, extra_turns

        synth = SingleSynthesizer(self.synthesizer_index)
        final, synth_extra = await synth.synthesize(counselors, discussion, turns)
        return final, extra_turns + synth_extra


def build_synthesis_engine(
    strategy: str,
    synthesizer_index: int = 0,
) -> SynthesisEngine:
    """Factory for synthesis engines from config string."""
    mapping: dict[str, type[SynthesisEngine]] = {
        "single": SingleSynthesizer,
        "last-round": SingleSynthesizer,
        "designated": SingleSynthesizer,
        "voting": VotingSynthesizer,
        "consensus": ConsensusChecker,
        "ranked": RankedSynthesizer,
    }
    cls = mapping.get(strategy, SingleSynthesizer)
    return cls(synthesizer_index=synthesizer_index)
