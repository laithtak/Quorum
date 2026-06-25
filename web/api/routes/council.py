"""Council configuration and deliberation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..session import SessionStore

router = APIRouter(prefix="/api/council", tags=["council"])


class ConfigureRequest(BaseModel):
    config: dict


class ConfigureResponse(BaseModel):
    session_id: str


class AskRequest(BaseModel):
    session_id: str
    query: str


class AskResponse(BaseModel):
    final_response: str
    turns: list[dict]
    usage: list[dict]
    total_cost_usd: float


def get_store() -> SessionStore:
    from ..main import store
    return store


@router.post("/configure", response_model=ConfigureResponse)
async def configure(req: ConfigureRequest) -> ConfigureResponse:
    session_id = get_store().create(req.config)
    return ConfigureResponse(session_id=session_id)


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    session = get_store().get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await session.orchestrator.deliberate(req.query)
    return AskResponse(
        final_response=result.final_response,
        turns=[
            {
                "counselor_name": t.counselor_name,
                "model": t.model,
                "round": t.round,
                "content": t.content,
            }
            for t in result.turns
        ],
        usage=[
            {
                "counselor_name": u.counselor_name,
                "model": u.model,
                "prompt_tokens": u.usage.prompt_tokens,
                "completion_tokens": u.usage.completion_tokens,
                "total_tokens": u.usage.total_tokens,
                "estimated_cost_usd": u.usage.estimated_cost_usd,
            }
            for u in result.usage
        ],
        total_cost_usd=result.total_cost_usd,
    )


@router.get("/config/{session_id}")
async def get_config(session_id: str) -> dict:
    session = get_store().get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.config


@router.put("/config/{session_id}")
async def update_config(session_id: str, req: ConfigureRequest) -> dict:
    if not get_store().update_config(session_id, req.config):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "ok"}
