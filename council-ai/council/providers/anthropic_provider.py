"""Anthropic provider for Claude models."""

from __future__ import annotations

from anthropic import AsyncAnthropic

from .base import BaseProvider, Message, ProviderConfig


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        kwargs: dict = {}
        if config.api_key:
            kwargs["api_key"] = config.api_key
        if config.base_url:
            kwargs["base_url"] = config.base_url
        self._client = AsyncAnthropic(**kwargs)

    async def complete(self, messages: list[Message]) -> str:
        # Anthropic separates system prompt from messages
        system_text = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_text += m.content + "\n"
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        # Ensure conversation starts with a user message
        if not chat_messages or chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Begin."})

        # Merge consecutive same-role messages (Anthropic requires alternating roles)
        merged: list[dict] = []
        for msg in chat_messages:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(msg)

        kwargs: dict = {
            "model": self.config.model,
            "messages": merged,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if system_text.strip():
            kwargs["system"] = system_text.strip()

        resp = await self._client.messages.create(**kwargs)
        return resp.content[0].text
