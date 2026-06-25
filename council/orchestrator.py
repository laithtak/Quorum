"""Orchestrator — runs the multi-round council deliberation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator

from .counselor import Counselor
from .providers.base import Message


class SynthesisStrategy(str, Enum):
    """How the final answer is produced after deliberation."""

    LAST_ROUND = "last-round"          # Dedicated synthesis by one counselor
    DESIGNATED = "designated"          # A specific counselor always synthesizes
    ROTATING = "rotating"              # Rotate who synthesizes each query


SYNTHESIS_PROMPT = (
    "The council has finished deliberating. "
    "Synthesize the discussion into a single, clear, final response for the user. "
    "Incorporate the strongest points from all counselors. "
    "Resolve any disagreements by choosing the best-supported position. "
    "Do NOT mention the council, the deliberation process, or individual counselors — "
    "respond as if you are giving the user a direct answer."
)


@dataclass
class TurnRecord:
    """Record of a single counselor's turn in the deliberation."""

    counselor_name: str
    model: str
    round: int
    content: str


@dataclass
class DeliberationResult:
    """Full result of a council deliberation."""

    query: str
    turns: list[TurnRecord] = field(default_factory=list)
    final_response: str = ""
    rounds_completed: int = 0

    @property
    def transcript(self) -> str:
        lines = [f"╭─ Query: {self.query}", "│"]
        current_round = 0
        for t in self.turns:
            if t.round != current_round:
                current_round = t.round
                lines.append(f"├─── Round {current_round} ───")
            lines.append(f"│ [{t.counselor_name} · {t.model}]")
            for line in t.content.strip().split("\n"):
                lines.append(f"│   {line}")
            lines.append("│")
        lines.append("├─── Final Response ───")
        for line in self.final_response.strip().split("\n"):
            lines.append(f"│ {line}")
        lines.append("╰──────────────────────")
        return "\n".join(lines)


class Orchestrator:
    """Manages the council deliberation process."""

    def __init__(
        self,
        counselors: list[Counselor],
        rounds: int = 2,
        synthesis: SynthesisStrategy = SynthesisStrategy.LAST_ROUND,
        synthesizer_index: int = 0,
        parallel_within_round: bool = False,
    ) -> None:
        if not counselors:
            raise ValueError("Council needs at least one counselor.")
        if rounds < 1:
            raise ValueError("Need at least 1 round of deliberation.")

        self.counselors = counselors
        self.rounds = rounds
        self.synthesis = synthesis
        self.synthesizer_index = synthesizer_index
        self.parallel_within_round = parallel_within_round

    async def deliberate(self, query: str) -> DeliberationResult:
        """Run the full deliberation and return the result."""
        result = DeliberationResult(query=query)
        discussion: list[Message] = [Message(role="user", content=query)]

        for round_num in range(1, self.rounds + 1):
            if self.parallel_within_round:
                responses = await self._run_round_parallel(discussion, round_num)
            else:
                responses = await self._run_round_sequential(discussion, round_num)

            for counselor, response in responses:
                turn = TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=round_num,
                    content=response,
                )
                result.turns.append(turn)
                discussion.append(
                    Message(role="assistant", content=f"[{counselor.name}]: {response}")
                )

            result.rounds_completed = round_num

        # Synthesis
        result.final_response = await self._synthesize(discussion)
        return result

    async def deliberate_stream(self, query: str) -> AsyncIterator[TurnRecord | str]:
        """Stream turns as they happen. Yields TurnRecords during deliberation,
        then yields the final response string."""
        discussion: list[Message] = [Message(role="user", content=query)]

        for round_num in range(1, self.rounds + 1):
            if self.parallel_within_round:
                responses = await self._run_round_parallel(discussion, round_num)
            else:
                responses = await self._run_round_sequential(discussion, round_num)

            for counselor, response in responses:
                turn = TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=round_num,
                    content=response,
                )
                discussion.append(
                    Message(role="assistant", content=f"[{counselor.name}]: {response}")
                )
                yield turn

        final = await self._synthesize(discussion)
        yield final

    async def _run_round_sequential(
        self, discussion: list[Message], round_num: int
    ) -> list[tuple[Counselor, str]]:
        """Each counselor responds one at a time, seeing previous responses."""
        results: list[tuple[Counselor, str]] = []
        current_discussion = list(discussion)

        for counselor in self.counselors:
            response = await counselor.respond(current_discussion)
            results.append((counselor, response))
            current_discussion.append(
                Message(role="assistant", content=f"[{counselor.name}]: {response}")
            )
        return results

    async def _run_round_parallel(
        self, discussion: list[Message], round_num: int
    ) -> list[tuple[Counselor, str]]:
        """All counselors respond simultaneously (they see the same context)."""
        tasks = [counselor.respond(list(discussion)) for counselor in self.counselors]
        responses = await asyncio.gather(*tasks)
        return list(zip(self.counselors, responses))

    async def _synthesize(self, discussion: list[Message]) -> str:
        """Produce the final synthesized response."""
        synthesizer = self.counselors[self.synthesizer_index % len(self.counselors)]

        synthesis_messages = list(discussion) + [
            Message(role="user", content=SYNTHESIS_PROMPT)
        ]
        return await synthesizer.respond(synthesis_messages)
