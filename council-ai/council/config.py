"""Configuration loader — reads council setup from YAML, JSON, or Python dicts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .counselor import Counselor, DEFAULT_PERSONA
from .orchestrator import Orchestrator, SynthesisStrategy
from .providers import create_provider
from .providers.base import ProviderConfig


def _resolve_env(value: str | None) -> str | None:
    """If value looks like ${ENV_VAR}, resolve it."""
    if value and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.environ.get(env_key)
    return value


def _parse_counselor(data: dict[str, Any], index: int) -> Counselor:
    """Parse a single counselor definition."""
    provider_cfg = ProviderConfig(
        provider=data["provider"],
        model=data["model"],
        api_key=_resolve_env(data.get("api_key")),
        base_url=_resolve_env(data.get("base_url")),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 1024),
    )
    provider = create_provider(provider_cfg)
    name = data.get("name", f"Counselor-{index + 1}")
    persona = data.get("persona", DEFAULT_PERSONA)
    return Counselor(name=name, provider=provider, persona=persona)


def load_config(path: str | Path) -> Orchestrator:
    """Load an Orchestrator from a config file (JSON or YAML)."""
    path = Path(path)
    text = path.read_text()

    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ImportError("Install PyYAML to use YAML configs: pip install pyyaml")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    return build_from_dict(data)


def build_from_dict(data: dict[str, Any]) -> Orchestrator:
    """Build an Orchestrator from a config dictionary."""
    counselors_data = data.get("counselors", [])
    if not counselors_data:
        raise ValueError("Config must define at least one counselor.")

    counselors = [_parse_counselor(c, i) for i, c in enumerate(counselors_data)]

    settings = data.get("settings", {})
    return Orchestrator(
        counselors=counselors,
        rounds=settings.get("rounds", 2),
        synthesis=SynthesisStrategy(settings.get("synthesis", "last-round")),
        synthesizer_index=settings.get("synthesizer_index", 0),
        parallel_within_round=settings.get("parallel", False),
    )


def build_quick(
    models: list[str],
    provider: str = "openai",
    rounds: int = 2,
    api_key: str | None = None,
    base_url: str | None = None,
) -> Orchestrator:
    """Quick helper to build a council from a list of model names on one provider."""
    counselors = []
    for i, model in enumerate(models):
        cfg = ProviderConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        p = create_provider(cfg)
        counselors.append(Counselor(name=f"Counselor-{i + 1}", provider=p))
    return Orchestrator(counselors=counselors, rounds=rounds)
