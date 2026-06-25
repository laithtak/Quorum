"""Provider registry — maps provider names to implementations."""

from __future__ import annotations

from .base import BaseProvider, ProviderConfig

_REGISTRY: dict[str, type[BaseProvider]] = {}


def _ensure_registry() -> None:
    """Lazy-import providers so missing SDK deps don't crash the whole package."""
    if _REGISTRY:
        return

    try:
        from .openai_provider import OpenAIProvider
        _REGISTRY["openai"] = OpenAIProvider
    except ImportError:
        pass

    try:
        from .anthropic_provider import AnthropicProvider
        _REGISTRY["anthropic"] = AnthropicProvider
    except ImportError:
        pass

    try:
        from .google_provider import GoogleProvider
        _REGISTRY["google"] = GoogleProvider
    except ImportError:
        pass

    try:
        from .ollama_provider import OllamaProvider
        _REGISTRY["ollama"] = OllamaProvider
    except ImportError:
        pass

    try:
        from .openrouter_provider import OpenRouterProvider
        _REGISTRY["openrouter"] = OpenRouterProvider
    except ImportError:
        pass


def create_provider(config: ProviderConfig) -> BaseProvider:
    """Create a provider instance from config."""
    _ensure_registry()
    provider_cls = _REGISTRY.get(config.provider)
    if provider_cls is None:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        raise ValueError(
            f"Unknown provider '{config.provider}'. Available: {available}. "
            f"Make sure the SDK is installed (e.g. pip install openai)."
        )
    return provider_cls(config)


def available_providers() -> list[str]:
    """Return names of providers whose SDKs are installed."""
    _ensure_registry()
    return sorted(_REGISTRY.keys())
