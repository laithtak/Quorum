"""Google Gemini provider."""

from __future__ import annotations

from google import genai
from google.genai import types

from ..usage import TokenUsage, calculate_cost
from .base import BaseProvider, CompletionResult, Message, ProviderConfig


class GoogleProvider(BaseProvider):
    """Provider for Google Gemini models."""

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self._client = genai.Client(api_key=config.api_key)

    async def complete(self, messages: list[Message]) -> CompletionResult:
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
        text = resp.text or ""
        usage = None
        if resp.usage_metadata:
            prompt = resp.usage_metadata.prompt_token_count or 0
            completion = resp.usage_metadata.candidates_token_count or 0
            usage = TokenUsage(
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=prompt + completion,
                estimated_cost_usd=calculate_cost(self.config.model, prompt, completion),
                model=self.config.model,
            )
        return CompletionResult(text=text, usage=usage)
