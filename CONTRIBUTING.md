# Contributing to Quorum

Thank you for your interest in contributing to Quorum!

## Development setup

```bash
cd council-ai
pip install -e ".[dev]"
```

Run lint and tests from `council-ai/`:

```bash
ruff check council/ tests/
pytest tests/ -v
```

Copy `.env.example` to `.env` at the repo root (or in `council-ai/`) and add API keys for the providers you test against.

## Pull requests

1. Fork the repository and create a feature branch.
2. Add tests for new behavior.
3. Ensure `ruff check` and `pytest` pass.
4. Update `CHANGELOG.md` for user-facing changes.
5. Open a PR with a clear description (the PR template includes a checklist).

## Code style

- Python 3.10+ with type hints
- Line length 100 (ruff)
- Match existing patterns in `council/`

## Adding a new provider

1. Create `council/providers/your_provider.py` implementing `BaseProvider`:

```python
from .base import BaseProvider, CompletionResult, Message, ProviderConfig

class YourProvider(BaseProvider):
    async def complete(self, messages: list[Message]) -> CompletionResult:
        # Call your API and return CompletionResult(text=..., usage=...)
        ...
```

2. Register it in `council/providers/__init__.py` inside `_ensure_registry()`:

```python
from .your_provider import YourProvider
_REGISTRY["your_provider"] = YourProvider
```

3. Add the SDK dependency to `pyproject.toml` if needed.
4. Add tests using `MockProvider` or a thin integration test with env-gated API calls.
5. Document the provider in the root `README.md` provider table.

## Adding a persona pack

1. Create `council/packs/your_pack.py` with:

```python
PACK_NAME = "your_pack"
PACK_DESCRIPTION = "Short description for council packs listing."
DEFAULT_SETTINGS = {"rounds": 2, "synthesis": "last-round"}

COUNSELOR_DEFS = [
    {"name": "Role A", "persona": "System prompt for this counselor."},
    {"name": "Role B", "persona": "..."},
]
```

2. Import the module and add an entry to `PACK_REGISTRY` in `council/packs/__init__.py`.
3. Add a test that `load_pack("your_pack")` returns the expected counselor count.
4. Mention the pack in `CHANGELOG.md`.

## Writing tests with MockProvider

`tests/conftest.py` defines `MockProvider`, a deterministic `BaseProvider` for unit tests:

```python
from tests.conftest import MockProvider
from council.counselor import Counselor

provider = MockProvider(response="Test answer.", fail=False)
counselor = Counselor(name="Test", provider=provider)
```

Fixtures are available:

- `mock_provider` — working provider with a canned response
- `failing_provider` — raises on every call (for retry/middleware tests)
- `make_counselor` — factory: `make_counselor(name="A", response="...", fail=False)`

Use `MockProvider` instead of live API calls so tests stay fast and key-free. Assert on `provider.call_count` and `provider.last_messages` when testing orchestration.

## Web UI

```bash
cd web
docker compose up
```

API on port 8000, frontend on port 3000.
