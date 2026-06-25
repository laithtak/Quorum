"""Base provider interface for LLM backends."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class Message:
    """A single message in the conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str
    name: str | None = None  # counselor name for display


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    provider: str  # "openai" | "anthropic" | "google" | "ollama"
    model: str
    api_key: str | None = None
    base_url: str | None = None  # for Ollama or custom endpoints
    temperature: float = 0.7
    max_tokens: int = 1024
    extra: dict = field(default_factory=dict)


class BaseProvider(abc.ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abc.abstractmethod
    async def complete(self, messages: list[Message]) -> str:
        """Send messages and return the assistant response text."""
        ...

    @property
    def model_name(self) -> str:
        return self.config.model

    @property
    def provider_name(self) -> str:
        return self.config.provider

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.config.model}>"
