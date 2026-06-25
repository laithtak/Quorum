"""Counselor — an AI model with a deliberation persona."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .providers.base import BaseProvider, CompletionResult, Message
from .usage import TokenUsage

if TYPE_CHECKING:
    from .middleware import MiddlewareStack


DEFAULT_PERSONA = (
    "You are a thoughtful counselor in a deliberation panel. "
    "You will see what other counselors have said. "
    "Engage critically: agree where warranted, challenge weak reasoning, "
    "add perspectives others missed, and refine the group's thinking. "
    "Be concise and substantive — no filler."
)


@dataclass
class Counselor:
    """A single counselor in the council."""

    name: str
    provider: BaseProvider
    persona: str = DEFAULT_PERSONA
    _history: list[Message] = field(default_factory=list, repr=False)
    _usage: TokenUsage = field(default_factory=TokenUsage, repr=False)
    middleware: MiddlewareStack | None = field(default=None, repr=False)

    @property
    def label(self) -> str:
        return f"{self.name} ({self.provider.model_name})"

    async def respond(self, discussion: list[Message]) -> str:
        """Generate this counselor's response given the discussion so far."""
        messages = [
            Message(role="system", content=self._build_system_prompt()),
            *discussion,
        ]

        async def _complete() -> CompletionResult:
            return await self.provider.complete(messages)

        if self.middleware:
            result = await self.middleware.run_complete(
                _complete,
                counselor_name=self.name,
                model=self.provider.model_name,
                provider_name=self.provider.provider_name,
                messages=messages,
            )
        else:
            result = await _complete()

        if result.usage:
            self._usage = self._usage + result.usage

        self._history.append(
            Message(role="assistant", content=result.text, name=self.name)
        )
        return result.text

    def get_usage(self) -> TokenUsage | None:
        if self._usage.total_tokens == 0 and self._usage.estimated_cost_usd == 0:
            return self._usage if self._usage.prompt_tokens else None
        return self._usage

    def reset_usage(self) -> None:
        self._usage = TokenUsage()

    def _build_system_prompt(self) -> str:
        return (
            f"Your name in this council is **{self.name}**.\n\n"
            f"{self.persona}\n\n"
            "When you respond, focus on the substance. "
            "Do not repeat what others said unless you're building on it."
        )
