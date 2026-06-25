"""In-memory session store for the web API."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from council.config import build_from_dict
from council.memory import ConversationMemory
from council.orchestrator import Orchestrator


@dataclass
class Session:
    orchestrator: Orchestrator
    memory: ConversationMemory
    config: dict[str, Any] = field(default_factory=dict)


class SessionStore:
    """Simple in-memory session manager."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, config: dict[str, Any]) -> str:
        session_id = str(uuid.uuid4())
        memory = ConversationMemory()
        orchestrator = build_from_dict(config)
        orchestrator.memory = memory
        self._sessions[session_id] = Session(
            orchestrator=orchestrator,
            memory=memory,
            config=config,
        )
        return session_id

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def update_config(self, session_id: str, config: dict[str, Any]) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        memory = session.memory
        orchestrator = build_from_dict(config)
        orchestrator.memory = memory
        session.orchestrator = orchestrator
        session.config = config
        return True

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
