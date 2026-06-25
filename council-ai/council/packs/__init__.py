"""Persona packs — pre-built counselor panels for common use cases."""

from __future__ import annotations

from . import brainstorm, code_review, debate, product, research

PACK_REGISTRY: dict[str, dict] = {
    debate.PACK_NAME: {
        "name": debate.PACK_NAME,
        "description": debate.PACK_DESCRIPTION,
        "counselor_defs": debate.COUNSELOR_DEFS,
        "default_settings": debate.DEFAULT_SETTINGS,
    },
    code_review.PACK_NAME: {
        "name": code_review.PACK_NAME,
        "description": code_review.PACK_DESCRIPTION,
        "counselor_defs": code_review.COUNSELOR_DEFS,
        "default_settings": code_review.DEFAULT_SETTINGS,
    },
    research.PACK_NAME: {
        "name": research.PACK_NAME,
        "description": research.PACK_DESCRIPTION,
        "counselor_defs": research.COUNSELOR_DEFS,
        "default_settings": research.DEFAULT_SETTINGS,
    },
    product.PACK_NAME: {
        "name": product.PACK_NAME,
        "description": product.PACK_DESCRIPTION,
        "counselor_defs": product.COUNSELOR_DEFS,
        "default_settings": product.DEFAULT_SETTINGS,
    },
    brainstorm.PACK_NAME: {
        "name": brainstorm.PACK_NAME,
        "description": brainstorm.PACK_DESCRIPTION,
        "counselor_defs": brainstorm.COUNSELOR_DEFS,
        "default_settings": brainstorm.DEFAULT_SETTINGS,
    },
}


def load_pack(name: str) -> dict:
    """Load a pack definition by name."""
    if name not in PACK_REGISTRY:
        available = ", ".join(sorted(PACK_REGISTRY.keys()))
        raise ValueError(f"Unknown pack '{name}'. Available: {available}")
    return PACK_REGISTRY[name]


def list_packs() -> list[dict]:
    """Return summary info for all packs."""
    return [
        {"name": p["name"], "description": p["description"]}
        for p in PACK_REGISTRY.values()
    ]
