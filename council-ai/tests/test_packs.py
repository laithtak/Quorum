"""Tests for persona packs."""

import pytest

from council.packs import list_packs, load_pack, PACK_REGISTRY
from council.config import build_from_dict, build_quick


def test_list_packs_returns_five():
    packs = list_packs()
    assert len(packs) == 5


def test_pack_registry_keys():
    assert set(PACK_REGISTRY.keys()) == {
        "debate", "code_review", "research", "product", "brainstorm"
    }


def test_load_pack_debate():
    pack = load_pack("debate")
    assert pack["name"] == "debate"
    assert len(pack["counselor_defs"]) == 3


def test_load_unknown_pack_raises():
    with pytest.raises(ValueError, match="Unknown pack"):
        load_pack("nonexistent")


def test_build_from_dict_with_pack():
    data = {
        "pack": "debate",
        "provider": "ollama",
        "model": "llama3.1",
        "settings": {"rounds": 1},
    }
    orch = build_from_dict(data)
    assert len(orch.counselors) == 3
    assert orch.counselors[0].name == "Advocate"


def test_build_quick_with_pack():
    orch = build_quick(["llama3.1"], provider="ollama", pack="debate", rounds=1)
    assert len(orch.counselors) == 3


def test_pack_counselor_overrides():
    data = {
        "pack": "product",
        "provider": "ollama",
        "model": "mistral",
        "counselors": [{"model": "llama3.1"}, {"name": "CustomEng"}],
    }
    orch = build_from_dict(data)
    assert orch.counselors[0].provider.model_name == "llama3.1"
    assert orch.counselors[1].name == "CustomEng"
