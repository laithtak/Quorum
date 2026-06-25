"""Google Gemini provider."""

from __future__ import annotations

from google import genai
from google.genai import types

from .base import BaseProvider, Message, ProviderConfig


class GoogleProvider(BaseProvider):
    """Provider for Google Gemini models."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = genai.Client(api_key=config.api_key)

    async def complete(self, messages: list[Message]) -> str:
        system_text = ""
        contents = []
        for m in messages:
            if m.role == "system":
                system_text += m.content + "\n"
            else:
                role = "user" if m.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=m.content)]))

        config = types.GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
        )
        if system_text.strip():
            config.system_instruction = system_text.strip()

        resp = await self._client.aio.models.generate_content(
            model=self.config.model,
            contents=contents,
            config=config,
        )
        return resp.text or ""
