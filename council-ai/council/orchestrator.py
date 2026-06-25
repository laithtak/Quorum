"""Orchestrator — runs the multi-round council deliberation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator

from .consensus import check_consensus
from .counselor import Counselor
from .memory import ConversationMemory
from .middleware import MiddlewareStack
from .providers.base import Message
from .models import TurnRecord
from .synthesis import SYNTHESIS_PROMPT, SynthesisEngine, SingleSynthesizer
from .usage import CounselorUsage

logger = logging.getLogger("council")

# Re-export TurnRecord for backward compatibility
__all__ = [
    "Orchestrator",
    "SynthesisStrategy",
    "DeliberationResult",
    "TurnRecord",
    "SYNTHESIS_PROMPT",
]


class SynthesisStrategy(str, Enum):
    """How the final answer is produced after deliberation."""

    LAST_ROUND = "last-round"
    DESIGNATED = "designated"
    ROTATING = "rotating"


@dataclass
class DeliberationResult:
    """Full result of a council deliberation."""

    query: str
    turns: list[TurnRecord] = field(default_factory=list)
    final_response: str = ""
    rounds_completed: int = 0
    usage: list[CounselorUsage] = field(default_factory=list)
    total_cost_usd: float = 0.0

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
        until_consensus: bool = False,
        max_rounds: int = 50,
        synthesis: SynthesisStrategy = SynthesisStrategy.LAST_ROUND,
        synthesizer_index: int = 0,
        parallel_within_round: bool = False,
        memory: ConversationMemory | None = None,
        middleware: MiddlewareStack | None = None,
        synthesis_engine: SynthesisEngine | None = None,
    ) -> None:
        if not counselors:
            raise ValueError("Council needs at least one counselor.")
        if not until_consensus and rounds < 1:
            raise ValueError("Need at least 1 round of deliberation.")
        if until_consensus and max_rounds < 1:
            raise ValueError("max_rounds must be at least 1 in until-consensus mode.")

        self.counselors = counselors
        self.rounds = rounds
        self.until_consensus = until_consensus
        self.max_rounds = max_rounds
        self.synthesis = synthesis
        self.synthesizer_index = synthesizer_index
        self.parallel_within_round = parallel_within_round
        self.memory = memory
        self.middleware = middleware
        self.synthesis_engine = synthesis_engine or SingleSynthesizer(
            synthesizer_index=synthesizer_index
        )

        if middleware:
            for counselor in self.counselors:
                counselor.middleware = middleware

    def _build_discussion(self, query: str) -> list[Message]:
        if self.memory:
            return self.memory.get_context() + [Message(role="user", content=query)]
        return [Message(role="user", content=query)]

    def _aggregate_usage(self) -> tuple[list[CounselorUsage], float]:
        usage_list: list[CounselorUsage] = []
        total_cost = 0.0
        for counselor in self.counselors:
            u = counselor.get_usage()
            if u and (u.total_tokens > 0 or u.estimated_cost_usd > 0):
                usage_list.append(
                    CounselorUsage(
                        counselor_name=counselor.name,
                        model=counselor.provider.model_name,
                        usage=u,
                    )
                )
                total_cost += u.estimated_cost_usd
        return usage_list, total_cost

    def _reset_usage(self) -> None:
        for counselor in self.counselors:
            counselor.reset_usage()

    async def _run_round(
        self, discussion: list[Message], round_num: int
    ) -> list[tuple[Counselor, str]]:
        if self.parallel_within_round:
            return await self._run_round_parallel(discussion, round_num)
        return await self._run_round_sequential(discussion, round_num)

    def _append_round_turns(
        self,
        responses: list[tuple[Counselor, str]],
        round_num: int,
        discussion: list[Message],
        turns: list[TurnRecord],
    ) -> None:
        for counselor, response in responses:
            turn = TurnRecord(
                counselor_name=counselor.name,
                model=counselor.provider.model_name,
                round=round_num,
                content=response,
            )
            turns.append(turn)
            discussion.append(
                Message(role="assistant", content=f"[{counselor.name}]: {response}")
            )

    async def _maybe_check_consensus(
        self,
        discussion: list[Message],
        round_num: int,
        turns: list[TurnRecord],
    ) -> bool:
        """Return True if deliberation should stop (consensus reached or cap hit)."""
        judge = self.counselors[self.synthesizer_index % len(self.counselors)]
        agreed, _verdict, consensus_turn = await check_consensus(
            judge, discussion, round_num
        )
        turns.append(consensus_turn)
        if agreed:
            return True
        if round_num >= self.max_rounds:
            logger.warning(
                "Reached max_rounds (%d) without consensus; proceeding to synthesis.",
                self.max_rounds,
            )
            return True
        return False

    async def deliberate(self, query: str) -> DeliberationResult:
        """Run the full deliberation and return the result."""
        self._reset_usage()
        result = DeliberationResult(query=query)
        discussion = self._build_discussion(query)

        if self.middleware:
            await self.middleware.before_deliberation(query, self.counselors)

        round_num = 0
        while True:
            round_num += 1
            responses = await self._run_round(discussion, round_num)
            self._append_round_turns(responses, round_num, discussion, result.turns)
            result.rounds_completed = round_num

            if self.until_consensus:
                if await self._maybe_check_consensus(discussion, round_num, result.turns):
                    break
            elif round_num >= self.rounds:
                break

        final, extra_turns = await self.synthesis_engine.synthesize(
            self.counselors, discussion, result.turns
        )
        result.turns.extend(extra_turns)
        result.final_response = final

        usage_list, total_cost = self._aggregate_usage()
        result.usage = usage_list
        result.total_cost_usd = total_cost

        if self.memory:
            self.memory.add_exchange(query, result.final_response)

        if self.middleware:
            await self.middleware.after_deliberation(query, result)

        return result

    async def deliberate_stream(self, query: str) -> AsyncIterator[TurnRecord | str]:
        """Stream turns as they happen. Yields TurnRecords during deliberation,
        then yields the final response string."""
        self._reset_usage()
        discussion = self._build_discussion(query)
        turns: list[TurnRecord] = []
        rounds_completed = 0

        if self.middleware:
            await self.middleware.before_deliberation(query, self.counselors)

        round_num = 0
        while True:
            round_num += 1
            responses = await self._run_round(discussion, round_num)
            for counselor, response in responses:
                turn = TurnRecord(
                    counselor_name=counselor.name,
                    model=counselor.provider.model_name,
                    round=round_num,
                    content=response,
                )
                turns.append(turn)
                discussion.append(
                    Message(role="assistant", content=f"[{counselor.name}]: {response}")
                )
                yield turn

            rounds_completed = round_num

            if self.until_consensus:
                agreed_or_cap = await self._maybe_check_consensus(
                    discussion, round_num, turns
                )
                yield turns[-1]
                if agreed_or_cap:
                    break
            elif round_num >= self.rounds:
                break

        final, extra_turns = await self.synthesis_engine.synthesize(
            self.counselors, discussion, turns
        )
        for turn in extra_turns:
            turns.append(turn)
            yield turn

        if self.memory:
            self.memory.add_exchange(query, final)

        if self.middleware:
            result = DeliberationResult(
                query=query,
                turns=turns,
                final_response=final,
                rounds_completed=rounds_completed,
            )
            usage_list, total_cost = self._aggregate_usage()
            result.usage = usage_list
            result.total_cost_usd = total_cost
            await self.middleware.after_deliberation(query, result)

        yield final

    async def _run_round_sequential(
        self, discussion: list[Message], round_num: int
    ) -> list[tuple[Counselor, str]]:
        """Each counselor responds one at a time, seeing previous responses."""
        results: list[tuple[Counselor, str]] = []
        current_discussion = list(discussion)

        for counselor in self.counselors:
            try:
                response = await counselor.respond(current_discussion)
            except Exception as exc:
                logger.warning(
                    "Counselor %s failed in round %d: %s", counselor.name, round_num, exc
                )
                response = f"[{counselor.name} was unable to respond this round.]"
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
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        results: list[tuple[Counselor, str]] = []
        for counselor, resp in zip(self.counselors, raw):
            if isinstance(resp, Exception):
                logger.warning(
                    "Counselor %s failed in round %d: %s", counselor.name, round_num, resp
                )
                results.append((counselor, f"[{counselor.name} was unable to respond this round.]"))
            else:
                results.append((counselor, resp))
        return results
