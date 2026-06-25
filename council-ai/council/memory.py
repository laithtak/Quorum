"""Conversation memory for multi-turn chat sessions."""

from __future__ import annotations

from .providers.base import Message


def _estimate_tokens(text: str) -> int:
    """Character-based token estimate (no LLM call)."""
    return len(text) // 4


class ConversationMemory:
    """Rolling conversation memory with automatic summarization."""

    def __init__(self, max_tokens: int = 8000) -> None:
        self.max_tokens = max_tokens
        self._exchanges: list[tuple[str, str]] = []

    def add_exchange(self, query: str, response: str) -> None:
        self._exchanges.append((query, response))

    def clear(self) -> None:
        self._exchanges.clear()

    def _messages_from_exchanges(self) -> list[Message]:
        messages: list[Message] = []
        for query, response in self._exchanges:
            messages.append(Message(role="user", content=query))
            messages.append(Message(role="assistant", content=response))
        return messages

    def _total_tokens(self, messages: list[Message]) -> int:
        return sum(_estimate_tokens(m.content) for m in messages)

    def _collapse_oldest_pair(self, messages: list[Message]) -> list[Message]:
        if len(messages) < 2:
            return messages
        oldest_user = messages[0].content
        oldest_asst = messages[1].content
        summary_chunk = f"User: {oldest_user}\nAssistant: {oldest_asst}"
        rest = messages[2:]
        if rest and rest[0].role == "system" and rest[0].content.startswith(
            "Prior conversation summary:"
        ):
            existing = rest[0].content.removeprefix("Prior conversation summary:\n")
            rest[0] = Message(
                role="system",
                content=f"Prior conversation summary:\n{existing}\n\n{summary_chunk}",
            )
            return rest
        return [
            Message(role="system", content=f"Prior conversation summary:\n{summary_chunk}"),
            *rest,
        ]

    def get_context(self) -> list[Message]:
        messages = self._messages_from_exchanges()
        while len(messages) > 2 and self._total_tokens(messages) > self.max_tokens:
            messages = self._collapse_oldest_pair(messages)
        return messages

    def to_dict(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "exchanges": [
                {"query": q, "response": r} for q, r in self._exchanges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConversationMemory:
        mem = cls(max_tokens=data.get("max_tokens", 8000))
        for ex in data.get("exchanges", []):
            mem.add_exchange(ex["query"], ex["response"])
        return mem
