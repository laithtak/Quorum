# 🏛️ Council AI

**Multi-model deliberation framework — AI models discuss before they respond.**

Instead of asking one model and hoping for the best, Council AI assembles a panel of AI counselors that **debate, challenge, and refine** each other's reasoning across multiple rounds before producing a single, synthesized response.

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
pip install -e .
```

### Option 1: CLI — One-liner

```bash
# With cloud models
council ask "What's the best database for time-series data?" \
  --models gpt-4o,gpt-4o-mini \
  --provider openai \
  --rounds 2

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

### Option 3: Interactive chat

```bash
council chat --config examples/mixed_providers.json
council chat --models llama3.1,mistral,qwen2 --provider ollama
```

### Option 4: Python SDK

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

Council AI uses JSON or YAML config files. API keys can reference environment variables with `${VAR_NAME}` syntax.

```json
{
  "settings": {
    "rounds": 2,
    "synthesis": "last-round",
    "parallel": false
  },
  "counselors": [
    {
      "name": "Atlas",
      "provider": "openai",
      "model": "gpt-4o",
      "api_key": "${OPENAI_API_KEY}",
      "temperature": 0.7,
      "persona": "You are a rigorous analytical thinker."
    },
    {
      "name": "Sage",
      "provider": "anthropic",
      "model": "claude-sonnet-4-6",
      "api_key": "${ANTHROPIC_API_KEY}",
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

### Supported Providers

| Provider | Models | API Key Required? |
|----------|--------|-------------------|
| `openai` | GPT-4o, GPT-4o-mini, o1, etc. | Yes |
| `anthropic` | Claude Sonnet, Opus, Haiku | Yes |
| `google` | Gemini 2.5 Flash/Pro | Yes |
| `ollama` | Llama 3.1, Mistral, Qwen, Phi, etc. | No (local) |

> Any OpenAI-compatible API (vLLM, LiteLLM, Together AI) works with the `openai` provider — just set `base_url`.

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `rounds` | `2` | Number of deliberation rounds |
| `synthesis` | `last-round` | How the final answer is produced |
| `synthesizer_index` | `0` | Which counselor synthesizes (index into counselors array) |
| `parallel` | `false` | Run counselors in parallel within each round |

### Counselor Options

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name (auto-generated if omitted) |
| `provider` | Yes | `openai`, `anthropic`, `google`, or `ollama` |
| `model` | Yes | Model identifier |
| `api_key` | Depends | API key or `${ENV_VAR}` reference |
| `base_url` | No | Custom endpoint URL |
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
council-ai/
├── council/
│   ├── __init__.py          # Public API
│   ├── cli.py               # Typer CLI
│   ├── config.py            # Config loading (JSON/YAML)
│   ├── counselor.py         # Counselor class
│   ├── orchestrator.py      # Deliberation engine
│   └── providers/
│       ├── __init__.py      # Provider registry
│       ├── base.py          # Abstract provider interface
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       ├── google_provider.py
│       └── ollama_provider.py
├── examples/
│   ├── mixed_providers.json # Cloud API config
│   ├── local_ollama.json    # Local-only config
│   └── basic_usage.py       # Python SDK examples
├── pyproject.toml
├── LICENSE
└── README.md
```

## Roadmap

- [ ] Web UI (FastAPI + React)
- [ ] Voting-based synthesis (majority wins)
- [ ] Confidence scoring per counselor
- [ ] Conversation memory across queries
- [ ] Token usage tracking and cost estimation
- [ ] Pre-built persona packs (Debate Team, Code Review Panel, etc.)
- [ ] Middleware hooks (logging, rate limiting, caching)
- [ ] OpenRouter provider (single key, many models)

## Contributing

Contributions welcome. Fork, branch, PR. Run `ruff check` before submitting.

```bash
pip install -e ".[dev]"
ruff check council/
pytest
```

## License

MIT — see [LICENSE](LICENSE).
