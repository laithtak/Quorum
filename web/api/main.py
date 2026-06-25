"""FastAPI application for Council AI web UI."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import council, providers, ws
from .session import SessionStore

load_dotenv()

store = SessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    store._sessions.clear()


app = FastAPI(
    title="Council AI",
    description="Multi-model deliberation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(council.router)
app.include_router(providers.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
