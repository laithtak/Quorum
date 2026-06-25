"""WebSocket streaming routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from council.models import TurnRecord

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{session_id}")
async def deliberation_stream(websocket: WebSocket, session_id: str) -> None:
    from ..main import store

    await websocket.accept()
    session = store.get(session_id)
    if not session:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            query = payload.get("query", "")
            if not query:
                await websocket.send_json({"type": "error", "message": "Missing query"})
                continue

            async for item in session.orchestrator.deliberate_stream(query):
                if isinstance(item, TurnRecord):
                    await websocket.send_json({
                        "type": "turn",
                        "counselor_name": item.counselor_name,
                        "model": item.model,
                        "round": item.round,
                        "content": item.content,
                    })
                else:
                    usage_list, total_cost = session.orchestrator._aggregate_usage()
                    await websocket.send_json({
                        "type": "final",
                        "content": item,
                        "usage": [
                            {
                                "counselor_name": u.counselor_name,
                                "model": u.model,
                                "prompt_tokens": u.usage.prompt_tokens,
                                "completion_tokens": u.usage.completion_tokens,
                                "total_tokens": u.usage.total_tokens,
                                "estimated_cost_usd": u.usage.estimated_cost_usd,
                            }
                            for u in usage_list
                        ],
                        "total_cost_usd": total_cost,
                    })
    except WebSocketDisconnect:
        pass
