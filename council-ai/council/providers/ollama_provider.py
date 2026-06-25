"""Ollama provider for local open-source models.

Uses Ollama's OpenAI-compatible API, so any model pulled into Ollama works:
  ollama pull llama3.1
  ollama pull mistral
  ollama pull qwen2
"""

from __future__ import annotations

from openai import AsyncOpenAI

from .base import BaseProvider, Message, ProviderConfig

DEFAULT_OLLAMA_URL = "http://localhost:11434/v1"


class OllamaProvider(BaseProvider):
    """Provider for locally-running Ollama models."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        base_url = config.base_url or DEFAULT_OLLAMA_URL
        # Ollama doesn't need a real key but the client requires one
        self._client = AsyncOpenAI(base_url=base_url, api_key="ollama")

    async def complete(self, messages: list[Message]) -> str:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=formatted,
            temperature=self.config.temperature,
        )
        return resp.choices[0].message.content or ""
