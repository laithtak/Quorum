"""OpenAI provider — also works with any OpenAI-compatible API (vLLM, LiteLLM, Together, etc.)."""

from __future__ import annotations

from openai import AsyncOpenAI

from .base import BaseProvider, Message, ProviderConfig


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI and OpenAI-compatible APIs."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        kwargs: dict = {}
        if config.api_key:
            kwargs["api_key"] = config.api_key
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self._client = AsyncOpenAI(**kwargs)

    async def complete(self, messages: list[Message]) -> str:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=formatted,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return resp.choices[0].message.content or ""
