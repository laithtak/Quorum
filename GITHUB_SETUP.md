# GitHub & PyPI Setup (manual steps)

The v1.0.0 release was pushed to `main` and tagged `v1.0.0`. Complete these one-time settings in the GitHub and PyPI UIs.

## GitHub repository settings

Open [https://github.com/laithtak/Quorum/settings](https://github.com/laithtak/Quorum/settings):

| Setting | Value |
|---------|-------|
| **Description** | Multi-model AI deliberation — models debate before responding |
| **Topics** | `ai`, `llm`, `multi-agent`, `deliberation`, `openai`, `anthropic`, `python`, `fastapi` |
| **Website** | (optional) `https://github.com/laithtak/Quorum#readme` |
| **Visibility** | Public (if not already) |

### Features

- Enable **Issues**
- Enable **Discussions** (optional, for Q&A)

### Branch protection (`main`)

Settings → Branches → Add rule:

- Require status checks: **CI** (`test` job)
- Require branches to be up to date before merging

### Social preview

The repo root `quorum-header.png` is suitable as the Open Graph image (Settings → General → Social preview).

### `gh` CLI (optional)

If you install [GitHub CLI](https://cli.github.com/):

```bash
gh auth login
gh repo edit laithtak/Quorum \
  --description "Multi-model AI deliberation — models debate before responding" \
  --add-topic ai --add-topic llm --add-topic multi-agent \
  --add-topic deliberation --add-topic openai --add-topic anthropic \
  --add-topic python --add-topic fastapi
```

## PyPI trusted publishing

The [release workflow](.github/workflows/release.yml) publishes to PyPI when a `v*` tag is pushed. One-time setup:

1. **Create PyPI account** at [pypi.org](https://pypi.org) (if needed).

2. **Register project** `council-ai` on PyPI (first upload can also be manual).

3. **Trusted publisher** (PyPI → Account → Publishing → Add):
   - PyPI project name: `council-ai`
   - Owner: `laithtak`
   - Repository: `Quorum`
   - Workflow: `release.yml`
   - Environment: `pypi`

4. **GitHub environment** (repo → Settings → Environments → `pypi`):
   - Create environment named `pypi` (matches `release.yml`)
   - Optional: restrict to `main` / tags only

5. **Re-run or re-tag** if the first `v1.0.0` push ran before trusted publishing was configured:
   ```bash
   # Only if the release workflow failed on PyPI publish
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   git tag -a v1.0.0 -m "Quorum v1.0.0"
   git push origin v1.0.0
   ```
   Do **not** force-push `main`.

6. After PyPI publish succeeds, add the PyPI badge to `README.md`:
   ```markdown
   [![PyPI](https://img.shields.io/pypi/v/council-ai)](https://pypi.org/project/council-ai/)
   ```

## Docker (GHCR)

The release workflow also pushes `ghcr.io/laithtak/quorum:latest` and `:v1.0.0`. Ensure **Actions** write permission is enabled (Settings → Actions → General → Workflow permissions → Read and write).

## Good first issues (optional)

Add label `good first issue` and create starter issues, e.g.:

- Add confidence scoring per counselor
- Add DeepSeek provider
- YAML config support via optional `pyyaml` extra
