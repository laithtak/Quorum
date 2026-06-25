# Changelog

All notable changes to Council AI (Quorum) are documented here.

## [1.0.0] — 2025-06-25

### Added
- **CI/CD**: GitHub Actions for test matrix (Python 3.10–3.12), release pipeline, Docker image
- **Web UI**: FastAPI backend with WebSocket streaming, React + Tailwind frontend
- **Persona packs**: `debate`, `code_review`, `research`, `product`, `brainstorm` with `council packs` CLI
- **Synthesis strategies**: `single`, `voting`, `consensus`, `ranked` engines
- **Middleware**: logging, retry, cache, rate limiting via config
- **OpenRouter provider**: unified multi-model API support
- **Token tracking**: per-counselor usage and cost estimation in CLI and API
- **Conversation memory**: rolling summary for `council chat` sessions

### Changed
- `BaseProvider.complete()` now returns `CompletionResult` with usage metadata
- `SynthesisStrategy` enum retained for backward compatibility; delegates to synthesis engines
- Canonical package root: `council-ai/`

## [0.5.0] — Web UI preview

- FastAPI + React web interface with docker-compose

## [0.4.0] — Synthesis & packs

- Synthesis engine classes and persona packs

## [0.3.0] — Middleware & OpenRouter

- Middleware stack and OpenRouter provider

## [0.2.0] — Memory & usage

- Conversation memory and token/cost tracking

## [0.1.0] — Initial release

- Multi-round orchestrator, OpenAI/Anthropic/Google/Ollama providers, CLI
