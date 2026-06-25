"""Tests for OpenRouter provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from council.providers.base import Message, ProviderConfig
from council.providers.openrouter_provider import OpenRouterProvider


@pytest.mark.asyncio
async def test_openrouter_complete_returns_result():
    config = ProviderConfig(
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
        api_key="test-key",
    )
    provider = OpenRouterProvider(config)

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 50
    mock_usage.total_tokens = 150

    mock_choice = MagicMock()
    mock_choice.message.content = "OpenRouter response"

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_resp.usage = mock_usage

    with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_resp
        result = await provider.complete([Message(role="user", content="Hello")])

    assert result.text == "OpenRouter response"
    assert result.usage is not None
    assert result.usage.prompt_tokens == 100
    assert result.usage.completion_tokens == 50
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_openrouter_uses_custom_base_url():
    config = ProviderConfig(
        provider="openrouter",
        model="openai/gpt-4o",
        api_key="key",
        base_url="https://custom.openrouter.test/v1",
    )
    with patch("council.providers.openrouter_provider.AsyncOpenAI") as mock_client_cls:
        mock_client_cls.return_value.chat.completions.create = AsyncMock()
        provider = OpenRouterProvider(config)
        assert provider._client is mock_client_cls.return_value
        mock_client_cls.assert_called_once()
        call_kwargs = mock_client_cls.call_args.kwargs
        assert call_kwargs["base_url"] == "https://custom.openrouter.test/v1"
