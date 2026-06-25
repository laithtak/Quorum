"""OpenRouter provider — unified API for many models."""

from __future__ import annotations

import os

from openai import AsyncOpenAI

from ..usage import usage_from_openai_response
from .base import BaseProvider, CompletionResult, Message, ProviderConfig

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter's multi-model API."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        api_key = config.api_key or os.environ.get("OPENROUTER_API_KEY")
        referer = config.extra.get("http_referer") or os.environ.get(
            "OPENROUTER_HTTP_REFERER", "https://github.com/laithtak/Quorum"
        )
        title = config.extra.get("x_title") or os.environ.get("OPENROUTER_X_TITLE", "Quorum")
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.base_url or DEFAULT_BASE_URL,
            default_headers={
                "HTTP-Referer": referer,
                "X-Title": title,
            },
        )

    async def complete(self, messages: list[Message]) -> CompletionResult:
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=formatted,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        text = resp.choices[0].message.content or ""
        usage = usage_from_openai_response(self.config.model, resp.usage)
        return CompletionResult(text=text, usage=usage)
