"""Tests for config loading and provider registry."""

import warnings

import pytest

from council.config import build_from_dict, build_quick, _resolve_env
from council.env_keys import resolve_api_key
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


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert resolve_api_key("openai") == "sk-test"


def test_resolve_api_key_ollama_returns_none():
    assert resolve_api_key("ollama") is None


def test_build_openai_counselor_without_env_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    data = {
        "counselors": [{"provider": "openai", "model": "gpt-4o"}],
    }
    with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
        build_from_dict(data)


def test_api_key_in_json_is_ignored(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    data = {
        "counselors": [
            {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-inline-should-not-be-used",
            },
        ],
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        orch = build_from_dict(data)
    assert any("api_key in config files is ignored" in str(w.message) for w in caught)
    assert orch.counselors[0].provider.config.api_key == "from-env"


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
