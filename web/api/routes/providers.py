"""Provider listing routes."""

from __future__ import annotations

from fastapi import APIRouter

from council.providers import available_providers
from council.packs import list_packs

router = APIRouter(prefix="/api", tags=["providers"])


@router.get("/providers")
async def list_providers() -> dict:
    return {"providers": available_providers()}


@router.get("/packs")
async def get_packs() -> dict:
    return {"packs": list_packs()}
