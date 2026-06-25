# Quorum — Getting Started & Publishing to GitHub

This guide walks you through running Quorum locally and publishing the project on GitHub.

**Repository:** [github.com/laithtak/Quorum](https://github.com/laithtak/Quorum)

**Naming note:** The product is **Quorum**. The CLI command is `council`, the PyPI package is `council-ai`, and the Python import is `council`.

---

## 1. Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | [git-scm.com](https://git-scm.com/) |
| **API key(s)** | OpenAI, Google, Anthropic, or OpenRouter — or **Ollama** for free local models |
| **Docker** (optional) | Only needed for the Web UI |

---

## 2. Clone the repository

```bash
git clone https://github.com/laithtak/Quorum.git
cd Quorum
```

If you already have the project locally, make sure you are in the repo root (the folder that contains `README.md`, `council-ai/`, and `web/`).

---

## 3. Install Quorum

All Python code lives in the `council-ai/` subdirectory.

```bash
cd council-ai
pip install -e .
```

**Optional extras:**

```bash
pip install -e ".[dev]"    # pytest, ruff (for development)
pip install -e ".[web]"    # FastAPI Web UI backend
pip install -e ".[yaml]"   # YAML config file support
```

Verify the CLI is available:

```bash
council providers
```

You should see a list of installed providers (`openai`, `google`, `ollama`, etc.).

---

## 4. Configure API keys

From the **repo root** (one level above `council-ai/`):

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and add the keys for the providers you plan to use. Config files no longer accept `api_key` fields — keys must live in `.env` only.

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
```

You only need keys for the providers you actually call. Ollama does not require a key.

**Important:** `.env` is gitignored. Never commit API keys to GitHub.

---

## 5. Run Quorum

### Quick test (OpenAI)

```bash
council ask "What is Redis?" --models gpt-4o-mini --provider openai --rounds 2
```

### Free local test (Ollama)

1. Install [Ollama](https://ollama.com) and pull a model: `ollama pull llama3.1`
2. Run:

```bash
cd council-ai
council ask "Explain transformers simply" --config examples/local_ollama.json
```

### Interactive chat (with memory for follow-up questions)

```bash
cd council-ai
council chat --models gpt-4o --provider openai
```

Type your questions. Enter `quit` or `exit` to leave.

### Persona packs (debate, code review, etc.)

```bash
council packs
council ask "Should we use microservices?" --pack debate --models gpt-4o --provider openai
```

### Mixed providers (config file)

```bash
cd council-ai
council ask "Design a fraud detection system" --config examples/mixed_providers.json
```

Requires the matching API keys in `.env`.

### Deliberation modes

Quorum supports two ways to control how long counselors debate:

| Mode | When to use |
|------|-------------|
| **Fixed rounds** (default) | You want exactly N rounds, then a synthesized answer |
| **Until consensus** | Counselors keep debating until they agree or a safety cap is reached |

**Fixed rounds (CLI):**

```bash
council ask "What is Redis?" --models gpt-4o --provider openai --rounds 3
```

**Until consensus (CLI):**

```bash
council ask "Should we adopt microservices?" \
  --models gpt-4o,gpt-4o-mini \
  --provider openai \
  --until-consensus --max-rounds 20
```

After each round, a designated counselor judges whether the panel agrees. Deliberation stops on YES or when `max_rounds` is hit (default **50**). CLI flags override settings in a config file.

**Until consensus (config file):**

```json
{
  "settings": {
    "until_consensus": true,
    "max_rounds": 20,
    "synthesis": "single"
  },
  "counselors": [
    { "name": "Proponent", "provider": "openai", "model": "gpt-4o" },
    { "name": "Opponent", "provider": "google", "model": "gemini-2.5-flash-lite" }
  ]
}
```

```bash
council ask "Your debate topic" --config my_debate.json
```

Use `"synthesis": "single"` with until-consensus mode for a polished final answer after agreement.

### CLI flags worth knowing

| Flag | Effect |
|------|--------|
| `--show` / `--quiet` | Show full deliberation vs. final answer only |
| `--no-usage` | Hide token/cost table |
| `--config path.json` | Use a JSON (or YAML) config file |
| `--rounds N` | Fixed deliberation rounds (overrides config when set) |
| `--until-consensus` | Loop until counselors agree |
| `--max-rounds N` | Cap for until-consensus mode (default 50) |

---

## 6. Web UI (optional)

Requires Docker.

```bash
cd web
docker compose up
```

- API: http://localhost:8000
- Frontend: http://localhost:3000

---

## 7. Run tests before you publish

From `council-ai/`:

```bash
pip install -e ".[dev]"
ruff check council/ tests/
pytest tests/ -v
```

All tests should pass. CI runs the same checks on every push to `main`.

---

## 8. Publish to GitHub

### First-time push (new fork or fresh machine)

```bash
# From repo root
git status
git add .
git commit -m "Your commit message"
git remote add origin https://github.com/laithtak/Quorum.git   # skip if already set
git branch -M main
git push -u origin main
```

### Push updates after changes

```bash
git add .
git commit -m "Describe your change"
git push origin main
```

### Check CI

After pushing, open [Actions](https://github.com/laithtak/Quorum/actions) and confirm the **CI** workflow passes (ruff + pytest on Python 3.10, 3.11, 3.12).

---

## 9. GitHub repository settings (one-time)

Open [Repository Settings](https://github.com/laithtak/Quorum/settings):

| Setting | Recommended value |
|---------|-------------------|
| **Visibility** | Public |
| **Description** | Multi-model AI deliberation — models debate before responding |
| **Topics** | `ai`, `llm`, `multi-agent`, `deliberation`, `openai`, `anthropic`, `python`, `fastapi` |
| **Issues** | Enabled |
| **Discussions** | Optional, for community Q&A |
| **Social preview** | Upload `quorum-header.png` from the repo root |

### Branch protection (recommended)

Settings → Branches → Add rule for `main`:

- Require status checks to pass (CI `test` job)
- Require branches to be up to date before merging

### GitHub CLI (optional)

```bash
gh auth login
gh repo edit laithtak/Quorum \
  --description "Multi-model AI deliberation — models debate before responding" \
  --add-topic ai --add-topic llm --add-topic multi-agent \
  --add-topic deliberation --add-topic openai --add-topic anthropic \
  --add-topic python --add-topic fastapi
```

---

## 10. Release a version (optional)

Quorum uses tag-based releases. Pushing a `v*` tag triggers the [release workflow](.github/workflows/release.yml) (PyPI + Docker image on GHCR).

```bash
git tag -a v1.0.0 -m "Quorum v1.0.0"
git push origin v1.0.0
```

### PyPI trusted publishing (one-time)

If you want `pip install council-ai` to work from PyPI:

1. Create an account at [pypi.org](https://pypi.org)
2. On PyPI → Account → Publishing → Add trusted publisher:
   - Project: `council-ai`
   - Owner: `laithtak`
   - Repository: `Quorum`
   - Workflow: `release.yml`
   - Environment: `pypi`
3. On GitHub → Settings → Environments → create environment named `pypi`
4. Push or re-push the tag to trigger the release workflow

### Docker image (GHCR)

The release workflow publishes to `ghcr.io/laithtak/quorum`. Ensure Actions has **Read and write** workflow permissions (Settings → Actions → General).

---

## 11. Pre-publish checklist

Before making the repo public or tagging a release, confirm:

- [ ] `.env` is **not** tracked (`git status` should not list it)
- [ ] No API keys in committed files (search for `sk-`, `sk-ant-`, `AIza`)
- [ ] `ruff check council/ tests/` passes locally
- [ ] `pytest tests/ -v` passes locally
- [ ] CI is green on `main`
- [ ] `README.md` renders correctly on GitHub (badges, install paths)
- [ ] `LICENSE` (MIT) is present at repo root

---

## 12. Project layout

```
Quorum/                     # Git repo root
├── README.md               # Main documentation (shown on GitHub)
├── GETTING_STARTED.md      # This file
├── LICENSE
├── .env.example            # Copy to .env — never commit .env
├── quorum-header.png
├── .github/workflows/      # CI and release automation
├── council-ai/             # Python package — run pip install here
│   ├── council/            # Source code
│   ├── examples/           # Sample configs
│   └── tests/
├── web/                    # FastAPI + React UI
└── Dockerfile              # CLI container image
```

---

## 13. Troubleshooting

| Problem | Fix |
|---------|-----|
| `council: command not found` | Re-run `pip install -e .` from `council-ai/`; ensure Python Scripts is on PATH |
| `Provide --config or --models` | Pass `--models gpt-4o --provider openai` or `--config examples/...` |
| OpenAI / Google auth errors | Check `.env` is in the **repo root** and keys are valid |
| Ollama connection refused | Run `ollama serve` and ensure models are pulled |
| CI fails on `pip install -e .` | Check `council-ai/pyproject.toml` is valid (classifiers belong under `[project]`, not `[project.urls]`) |
| PyPI release fails | Complete trusted publishing setup (Section 10) before pushing tags |

---

## 14. Further reading

- [README.md](README.md) — features, configuration reference, architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute
- [CHANGELOG.md](CHANGELOG.md) — version history
- [GITHUB_SETUP.md](GITHUB_SETUP.md) — condensed GitHub/PyPI admin steps
