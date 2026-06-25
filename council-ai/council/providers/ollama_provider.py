"""Ollama provider for local open-source models.

Uses Ollama's OpenAI-compatible API, so any model pulled into Ollama works:
  ollama pull llama3.1
  ollama pull mistral
  ollama pull qwen2
"""

from __future__ import annotations

from openai import AsyncOpenAI

from ..usage import TokenUsage, usage_from_openai_response
from .base import BaseProvider, CompletionResult, Message, ProviderConfig

DEFAULT_OLLAMA_URL = "http://localhost:11434/v1"


class OllamaProvider(BaseProvider):
    """Provider for locally-running Ollama models."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        base_url = config.base_url or DEFAULT_OLLAMA_URL
        self._client = AsyncOpenAI(base_url=base_url, api_key="ollama")

    async def complete(self, messages: list[Message]) -> CompletionResult:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=formatted,
            temperature=self.config.temperature,
        )
        text = resp.choices[0].message.content or ""
        usage = usage_from_openai_response(self.config.model, resp.usage)
        if usage:
            usage.estimated_cost_usd = 0.0
        else:
            usage = TokenUsage(model=self.config.model, estimated_cost_usd=0.0)
        return CompletionResult(text=text, usage=usage)
