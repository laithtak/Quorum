"""Central API key resolution from environment variables only."""

from __future__ import annotations

import os

PROVIDER_ENV_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

_dotenv_loaded = False


def ensure_dotenv_loaded() -> None:
    """Call load_dotenv() once (find .env walking up from cwd)."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    _dotenv_loaded = True


def provider_requires_key(provider: str) -> bool:
    """Return True if the provider needs an API key from the environment."""
    return provider in PROVIDER_ENV_KEYS


def resolve_api_key(provider: str) -> str | None:
    """Read API key for provider from os.environ only."""
    ensure_dotenv_loaded()
    env_var = PROVIDER_ENV_KEYS.get(provider)
    if env_var is None:
        return None
    return os.environ.get(env_var)
