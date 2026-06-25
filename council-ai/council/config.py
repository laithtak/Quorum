"""Configuration loader — reads council setup from YAML, JSON, or Python dicts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .counselor import Counselor, DEFAULT_PERSONA
from .middleware import MiddlewareStack
from .middleware.cache_mw import CacheMiddleware
from .middleware.logging_mw import LoggingMiddleware
from .middleware.rate_limit_mw import RateLimitMiddleware
from .middleware.retry_mw import RetryMiddleware
from .models import TurnRecord  # noqa: F401 — re-export for tests
from .orchestrator import Orchestrator, SynthesisStrategy
from .packs import load_pack
from .providers import create_provider
from .providers.base import ProviderConfig
from .synthesis import build_synthesis_engine


def _resolve_env(value: str | None) -> str | None:
    """If value looks like ${ENV_VAR}, resolve it."""
    if value and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.environ.get(env_key)
    return value


def build_middleware_stack(config_list: list[dict[str, Any]]) -> MiddlewareStack:
    """Build a middleware stack from config entries."""
    middlewares = []
    for entry in config_list:
        mtype = entry.get("type", "")
        if mtype == "logging":
            middlewares.append(LoggingMiddleware())
        elif mtype == "retry":
            middlewares.append(
                RetryMiddleware(
                    max_retries=entry.get("max_retries", 3),
                    backoff=entry.get("backoff", 1.5),
                )
            )
        elif mtype == "cache":
            middlewares.append(
                CacheMiddleware(
                    backend=entry.get("backend", "memory"),
                    cache_dir=entry.get("cache_dir", ".council_cache"),
                )
            )
        elif mtype == "rate_limit":
            middlewares.append(
                RateLimitMiddleware(
                    rate=entry.get("rate", 10.0),
                    capacity=entry.get("capacity", 10.0),
                )
            )
    return MiddlewareStack(middlewares)


def _parse_counselor(data: dict[str, Any], index: int) -> Counselor:
    """Parse a single counselor definition."""
    provider_cfg = ProviderConfig(
        provider=data["provider"],
        model=data["model"],
        api_key=_resolve_env(data.get("api_key")),
        base_url=_resolve_env(data.get("base_url")),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 1024),
        extra=data.get("extra", {}),
    )
    provider = create_provider(provider_cfg)
    name = data.get("name", f"Counselor-{index + 1}")
    persona = data.get("persona", DEFAULT_PERSONA)
    return Counselor(name=name, provider=provider, persona=persona)


def _build_counselors_from_pack(
    pack_name: str,
    provider: str,
    model: str,
    overrides: list[dict[str, Any]] | None = None,
) -> list[Counselor]:
    """Build counselors from a persona pack with optional per-counselor overrides."""
    pack = load_pack(pack_name)
    overrides = overrides or []
    counselors = []
    for i, cdef in enumerate(pack["counselor_defs"]):
        override = overrides[i] if i < len(overrides) else {}
        data = {
            "provider": override.get("provider", provider),
            "model": override.get("model", model),
            "name": override.get("name", cdef["name"]),
            "persona": override.get("persona", cdef["persona"]),
            "api_key": override.get("api_key"),
            "base_url": override.get("base_url"),
            "temperature": override.get("temperature", 0.7),
            "max_tokens": override.get("max_tokens", 1024),
        }
        counselors.append(_parse_counselor(data, i))
    return counselors


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
    settings = dict(data.get("settings", {}))
    middleware_cfg = data.get("middleware", [])
    middleware = build_middleware_stack(middleware_cfg) if middleware_cfg else None

    if "pack" in data:
        pack_name = data["pack"]
        pack = load_pack(pack_name)
        settings = {**pack["default_settings"], **settings}
        provider = data.get("provider", "openai")
        model = data.get("model", "gpt-4o")
        overrides = data.get("counselors", [])
        counselors = _build_counselors_from_pack(pack_name, provider, model, overrides)
    else:
        counselors_data = data.get("counselors", [])
        if not counselors_data:
            raise ValueError("Config must define at least one counselor or a pack.")
        counselors = [_parse_counselor(c, i) for i, c in enumerate(counselors_data)]

    synthesis_str = settings.get("synthesis", "last-round")
    synthesizer_index = settings.get("synthesizer_index", 0)
    synthesis_engine = build_synthesis_engine(synthesis_str, synthesizer_index)

    try:
        synthesis_enum = SynthesisStrategy(synthesis_str)
    except ValueError:
        synthesis_enum = SynthesisStrategy.LAST_ROUND

    return Orchestrator(
        counselors=counselors,
        rounds=settings.get("rounds", 2),
        synthesis=synthesis_enum,
        synthesizer_index=synthesizer_index,
        parallel_within_round=settings.get("parallel", False),
        middleware=middleware,
        synthesis_engine=synthesis_engine,
    )


def build_quick(
    models: list[str],
    provider: str = "openai",
    rounds: int = 2,
    api_key: str | None = None,
    base_url: str | None = None,
    pack: str | None = None,
) -> Orchestrator:
    """Quick helper to build a council from a list of model names on one provider."""
    if pack:
        data = {
            "pack": pack,
            "provider": provider,
            "model": models[0] if models else "gpt-4o",
            "settings": {"rounds": rounds},
        }
        if len(models) > 1:
            data["counselors"] = [{"model": m} for m in models]
        return build_from_dict(data)

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
