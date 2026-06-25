"""Cache middleware — memoize completions by model + messages hash."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..providers.base import CompletionResult, Message
from . import CompleteFn, Middleware


def _cache_key(model: str, messages: list[Message]) -> str:
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class CacheMiddleware(Middleware):
    """Cache completion results in memory or on disk."""

    def __init__(self, backend: str = "memory", cache_dir: str = ".council_cache") -> None:
        self.backend = backend
        self.cache_dir = Path(cache_dir)
        self._memory: dict[str, CompletionResult] = {}
        if backend == "disk":
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get(self, key: str) -> CompletionResult | None:
        if self.backend == "memory":
            return self._memory.get(key)
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return CompletionResult(text=data["text"])

    def _set(self, key: str, result: CompletionResult) -> None:
        if self.backend == "memory":
            self._memory[key] = result
            return
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps({"text": result.text}))

    def wrap(
        self,
        complete_fn: CompleteFn,
        *,
        counselor_name: str,
        model: str,
        provider_name: str,
        messages: list[Message],
    ) -> CompleteFn:
        key = _cache_key(model, messages)

        async def wrapped() -> CompletionResult:
            cached = self._get(key)
            if cached is not None:
                return cached
            result = await complete_fn()
            self._set(key, result)
            return result

        return wrapped
