"""Counselor — an AI model with a deliberation persona."""

from __future__ import annotations

from dataclasses import dataclass, field

from .providers.base import BaseProvider, Message


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

    @property
    def label(self) -> str:
        return f"{self.name} ({self.provider.model_name})"

    async def respond(self, discussion: list[Message]) -> str:
        """Generate this counselor's response given the discussion so far."""
        messages = [
            Message(role="system", content=self._build_system_prompt()),
            *discussion,
        ]
        response = await self.provider.complete(messages)
        self._history.append(Message(role="assistant", content=response, name=self.name))
        return response

    def _build_system_prompt(self) -> str:
        return (
            f"Your name in this council is **{self.name}**.\n\n"
            f"{self.persona}\n\n"
            "When you respond, focus on the substance. "
            "Do not repeat what others said unless you're building on it."
        )
