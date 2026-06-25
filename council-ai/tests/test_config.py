"""Tests for config loading and provider registry."""

import pytest

from council.config import build_from_dict, build_quick, _resolve_env
from council.providers import available_providers


def test_resolve_env_with_var(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret123")
    assert _resolve_env("${TEST_KEY}") == "secret123"


def test_resolve_env_missing_var():
    assert _resolve_env("${NONEXISTENT_VAR_XYZ}") is None


def test_resolve_env_plain_string():
    assert _resolve_env("plain-value") == "plain-value"


def test_resolve_env_none():
    assert _resolve_env(None) is None


def test_build_from_dict_minimal():
    data = {
        "counselors": [
            {"provider": "ollama", "model": "llama3.1"},
        ],
    }
    orch = build_from_dict(data)
    assert len(orch.counselors) == 1
    assert orch.rounds == 2  # default


def test_build_from_dict_custom_settings():
    data = {
        "settings": {"rounds": 5, "parallel": True},
        "counselors": [
            {"provider": "ollama", "model": "a", "name": "Alpha"},
            {"provider": "ollama", "model": "b", "name": "Beta"},
        ],
    }
    orch = build_from_dict(data)
    assert orch.rounds == 5
    assert orch.parallel_within_round is True
    assert orch.counselors[0].name == "Alpha"
    assert orch.counselors[1].name == "Beta"


def test_build_from_dict_no_counselors_raises():
    with pytest.raises(ValueError, match="at least one"):
        build_from_dict({"counselors": []})


def test_build_quick():
    orch = build_quick(["model-a", "model-b"], provider="ollama", rounds=3)
    assert len(orch.counselors) == 2
    assert orch.rounds == 3


def test_available_providers_returns_list():
    providers = available_providers()
    assert isinstance(providers, list)
    # At minimum, ollama reuses openai SDK so both should be available
    assert "openai" in providers or "ollama" in providers
