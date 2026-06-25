<p align="center">
  <img src="quorum-header.png" alt="Quorum — Models deliberate together" width="100%"/>
</p>

[![CI](https://github.com/laithtak/Quorum/actions/workflows/ci.yml/badge.svg)](https://github.com/laithtak/Quorum/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

# Quorum

**Multi-model deliberation framework — models debate before they respond.**

*Models deliberate together before they respond.*

Instead of asking one model and hoping for the best, Quorum assembles a panel of AI counselors that **debate, challenge, and refine** each other's reasoning across multiple rounds before producing a single, synthesized response.

> **Note:** The CLI command is `council` and the PyPI package is `council-ai`. The Python import is `council`. These names are stable for v1.0.

```
You → "How should I architect a real-time fraud detection system?"
        ↓
  ┌─────────────────── Round 1 ───────────────────┐
  │  Atlas (GPT-4o):    System design analysis     │
  │  Sage  (Claude):    Edge cases & ethics        │
  │  Nova  (Gemini):    Practical trade-offs       │
  └────────────────────────────────────────────────┘
        ↓
  ┌─────────────────── Round 2 ───────────────────┐
  │  Atlas: Responds to Sage's privacy concerns    │
  │  Sage:  Builds on Nova's latency suggestion    │
  │  Nova:  Challenges Atlas's cost assumptions    │
  └────────────────────────────────────────────────┘
        ↓
  Synthesized final response → You
```

## Why?

- **Better answers** — Multiple perspectives catch blind spots a single model misses.
- **Reduced hallucination** — Models fact-check each other during deliberation.
- **Diverse reasoning** — Mix analytical, creative, and pragmatic thinkers.
- **Your models, your rules** — Use any combination of cloud APIs and local models.

## Quickstart

### Install

```bash
pip install council-ai
# or from source:
cd council-ai
pip install -e .
```

For web UI support: `pip install -e ".[web]"` (from `council-ai/`)

### Option 1: CLI — One-liner

```bash
# With cloud models (fixed rounds)
council ask "What's the best database for time-series data?" \
  --models gpt-4o,gpt-4o-mini \
  --provider openai \
  --rounds 2

# Until counselors agree (safety cap default 50)
council ask "Should we adopt microservices?" \
  --models gpt-4o,gpt-4o-mini \
  --provider openai \
  --until-consensus --max-rounds 10

# With local models (Ollama)
council ask "Explain transformers simply" \
  --models llama3.1,mistral \
  --provider ollama \
  --rounds 2
```

### Option 2: Config file — Full control

```bash
council ask "Design a microservices architecture" --config examples/mixed_providers.json
```

### Option 3: Interactive chat (with memory)

```bash
council chat --config examples/mixed_providers.json
council chat --models llama3.1,mistral,qwen2 --provider ollama
council chat --pack debate --models gpt-4o --provider openai
```

Chat sessions use **conversation memory** with rolling summarization so follow-up questions retain context.

### Option 4: Persona packs

```bash
council packs
council ask "Should we adopt microservices?" --pack debate --models gpt-4o --provider openai
```

Available packs: `debate`, `code_review`, `research`, `product`, `brainstorm`.

### Option 5: Python SDK

```python
import asyncio
from council import build_quick

async def main():
    orchestrator = build_quick(
        models=["gpt-4o", "gpt-4o-mini"],
        provider="openai",
        rounds=2,
    )
    result = await orchestrator.deliberate("What causes inflation?")
    print(result.final_response)

asyncio.run(main())
```

## Configuration

Quorum uses JSON or YAML config files. **API keys are read only from `.env`** — not from config files. Copy `.env.example` to `.env` and add the keys for providers you use.

```json
{
  "settings": {
    "rounds": 2,
    "until_consensus": false,
    "max_rounds": 50,
    "synthesis": "last-round",
    "parallel": false
  },
  "counselors": [
    {
      "name": "Atlas",
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.7,
      "persona": "You are a rigorous analytical thinker."
    },
    {
      "name": "Sage",
      "provider": "anthropic",
      "model": "claude-sonnet-4-6",
      "persona": "You focus on nuance, edge cases, and ethics."
    },
    {
      "name": "Local",
      "provider": "ollama",
      "model": "llama3.1",
      "persona": "You champion open-source and privacy-first solutions."
    }
  ]
}
```

### Deliberation modes

| Mode | Config / CLI | Behavior |
|------|--------------|----------|
| Fixed (default) | `"rounds": 5` or `--rounds 5` | Exactly 5 rounds, then synthesize |
| Until consensus | `"until_consensus": true` or `--until-consensus` | Loop until the judge agrees or `max_rounds` is hit |

Use `"synthesis": "single"` (default when `until_consensus` is true) with until-consensus mode. CLI flags override config file settings.

### Supported Providers

| Provider | Models | API Key Required? |
|----------|--------|-------------------|
| `openai` | GPT-4o, GPT-4o-mini, o1, etc. | Yes |
| `anthropic` | Claude Sonnet, Opus, Haiku | Yes |
| `google` | Gemini 2.5 Flash/Pro | Yes |
| `ollama` | Llama 3.1, Mistral, Qwen, Phi, etc. | No (local) |
| `openrouter` | 100+ models via unified API | Yes |

> Any OpenAI-compatible API (vLLM, LiteLLM, Together AI) works with the `openai` provider — just set `base_url`.

### Token usage & cost

Both `ask` and `chat` print a usage table after deliberation. Suppress with `--no-usage`.

### Synthesis strategies

| Strategy | Description |
|----------|-------------|
| `single` / `last-round` | Designated counselor synthesizes (default) |
| `voting` | Counselors vote on the best last-round response |
| `consensus` | Extra round if no consensus detected |
| `ranked` | Borda-count ranking of responses |

### Middleware

Optional middleware in config:

```json
"middleware": [
  {"type": "logging"},
  {"type": "retry", "max_retries": 3, "backoff": 1.5},
  {"type": "cache", "backend": "memory"}
]
```

### Web UI

```bash
cd web
docker compose up
```

- API: http://localhost:8000
- Frontend: http://localhost:3000

Configure counselors, stream deliberation in real time, and export/import JSON config.

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `rounds` | `2` | Fixed mode: exact number of deliberation rounds |
| `until_consensus` | `false` | Loop until counselors agree (ignores `rounds` for looping) |
| `max_rounds` | `50` | Safety cap when `until_consensus` is true |
| `synthesis` | `last-round` | How the final answer is produced |
| `synthesizer_index` | `0` | Which counselor synthesizes (index into counselors array) |
| `parallel` | `false` | Run counselors in parallel within each round |

### Counselor Options

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (auto-generated if omitted) |
| `provider` | Yes | `openai`, `anthropic`, `google`, `ollama`, or `openrouter` |
| `model` | Yes | Model identifier |
| `base_url` | No | Custom endpoint URL (supports `${ENV_VAR}` for non-secret values) |
| `temperature` | No | Sampling temperature (default: 0.7) |
| `max_tokens` | No | Max response tokens (default: 1024) |
| `persona` | No | System prompt defining this counselor's thinking style |

## How It Works

```
                    ┌─────────────┐
                    │  User Query │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │     Round 1             │
              │  Each counselor sees    │
              │  the query + previous   │
              │  counselors' responses  │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │     Round 2             │
              │  Each counselor sees    │
              │  ALL prior discussion   │
              │  and builds on it       │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │     Synthesis           │
              │  One counselor merges   │
              │  all perspectives into  │
              │  a final response       │
              └────────────┬────────────┘
                           │
                    ┌──────▼──────┐
                    │   Response  │
                    └─────────────┘
```

**Sequential mode** (default): Within each round, counselors respond one at a time. Each sees what came before, creating a true conversation.

**Parallel mode**: Within each round, all counselors respond simultaneously to the same context. Faster, but no intra-round interaction.

## Advanced: Python SDK

### Streaming deliberation

```python
from council import build_quick, TurnRecord

async def stream():
    orchestrator = build_quick(["gpt-4o", "gpt-4o-mini"], rounds=2)

    async for item in orchestrator.deliberate_stream("Your question"):
        if isinstance(item, TurnRecord):
            print(f"[{item.counselor_name}] {item.content[:100]}...")
        else:
            print(f"Final: {item}")
```

### Custom counselors with mixed providers

```python
from council import Counselor, Orchestrator, ProviderConfig, create_provider

counselors = [
    Counselor(
        name="Strategist",
        provider=create_provider(ProviderConfig(provider="openai", model="gpt-4o")),
        persona="Think like a McKinsey consultant. Data-driven, structured.",
    ),
    Counselor(
        name="Contrarian",
        provider=create_provider(ProviderConfig(provider="ollama", model="llama3.1")),
        persona="Challenge every assumption. Play devil's advocate.",
    ),
    Counselor(
        name="Pragmatist",
        provider=create_provider(ProviderConfig(provider="anthropic", model="claude-sonnet-4-6")),
        persona="Focus on what's actually achievable in the next 30 days.",
    ),
]

orchestrator = Orchestrator(counselors=counselors, rounds=3)
result = await orchestrator.deliberate("Should we rewrite our monolith?")
```

### Access the full transcript

```python
result = await orchestrator.deliberate("Your question")

# Formatted transcript
print(result.transcript)

# Structured access
for turn in result.turns:
    print(f"Round {turn.round} | {turn.counselor_name} | {turn.model}")
    print(turn.content)
```

## Local-Only Setup (Zero Cloud Dependencies)

Run entirely on your machine with [Ollama](https://ollama.com):

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull models
ollama pull llama3.1
ollama pull mistral
ollama pull qwen2

# 3. Run council
council chat --models llama3.1,mistral,qwen2 --provider ollama
```

## Project Structure

```
Quorum/                     # repo root
├── council-ai/             # Python package (pip install -e council-ai)
│   ├── council/
│   │   ├── memory.py       # Conversation memory
│   │   ├── usage.py        # Token/cost tracking
│   │   ├── synthesis.py    # Synthesis engines
│   │   ├── middleware/     # Logging, retry, cache, rate limit
│   │   ├── packs/          # Persona packs
│   │   └── providers/      # openai, anthropic, google, ollama, openrouter
│   ├── examples/
│   └── tests/
├── web/                    # FastAPI + React UI
├── Dockerfile              # CLI container image
└── README.md
```

## Roadmap

- [x] Web UI (FastAPI + React)
- [x] Voting-based synthesis
- [x] Conversation memory across queries
- [x] Token usage tracking and cost estimation
- [x] Pre-built persona packs
- [x] Middleware hooks (logging, rate limiting, caching)
- [ ] Confidence scoring per counselor
- [ ] YAML config support (install `pyyaml`)

## Open Source

Quorum is released under the [MIT License](LICENSE).

- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Security:** Report vulnerabilities via [SECURITY.md](SECURITY.md) or [GitHub Security Advisories](https://github.com/laithtak/Quorum/security/advisories/new)
- **Issues & discussions:** [Issues](https://github.com/laithtak/Quorum/issues) · [Discussions](https://github.com/laithtak/Quorum/discussions)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run from `council-ai/`:

```bash
pip install -e ".[dev]"
ruff check council/ tests/
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).
