---
date: 2026-04-01
title: "PEP 735 [dependency-groups] is uv-only; pip silently ignores them"
category: "build-errors"
language: "Python"
tags: [uv, pip, pep735, dependency-groups, pyproject-toml, optional-dependencies, packaging]
root-cause: "PEP 735 [dependency-groups] is a uv/PEP 735 extension. pip install .[dev] silently ignores the groups, leaving contributors with an incomplete environment and no error."
severity: "P2"
---

# PEP 735 `[dependency-groups]` Is uv-Only — pip Silently Ignores Them

## Problem

Defining dev or docs dependencies under `[dependency-groups]` in `pyproject.toml`
(PEP 735 syntax) works perfectly with `uv sync --group dev`, but contributors or
CI runners using plain `pip` get an incomplete environment with no error:

```
$ pip install ".[dev]"
Successfully installed povineq-0.1.0
# No pytest, no ruff, no mypy installed — [dependency-groups] silently ignored
```

Additionally, if `dev` and `docs` are placed under `[project.optional-dependencies]`
instead to work around this, those extras are published to PyPI, creating a confusing
`pip install povineq[dev]` public entry point for user-facing package extras.

## Root Cause

`[dependency-groups]` is specified in PEP 735 and supported by `uv` and `pdm`, but
NOT yet implemented in pip or the PEP 517/518 build backend machinery. It is a
**separate namespace** from `[project.optional-dependencies]`. PEP 517-compliant
tools (pip, build, twine) simply skip unknown tables; no warning is raised.

## Solution

Use the hybrid pattern: `[dependency-groups]` for dev/docs tooling (uv-only, not
published), `[project.optional-dependencies]` only for user-facing extras:

```toml
# pyproject.toml

# [USER-FACING — published to PyPI as pip install package[polars]]
[project.optional-dependencies]
polars = ["polars>=0.20"]

# [DEV/DOCS TOOLING — uv-only, NOT published to PyPI]
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "httpx>=0.27",
    "respx>=0.21",
    "ruff>=0.3",
    "mypy>=1.9",
]
docs = [
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.24",
    "mkdocs-gen-files>=0.5",
    "mkdocs-literate-nav>=0.6",
]
```

**Install commands:**
```bash
uv sync --group dev           # dev only
uv sync --group docs          # docs only
uv sync --group dev --group docs  # both
```

**If pip compatibility is required** (e.g., contributor setup without uv), document
it explicitly in README/CONTRIBUTING:
```markdown
> **Tooling requires uv.** Install with `pip install uv`, then `uv sync --group dev`.
> Plain `pip install ".[dev]"` will NOT install development dependencies.
```

## Prevention

- Never put dev/docs tooling under `[project.optional-dependencies]` — it pollutes
  PyPI's extras surface.
- Never put user-facing extras under `[dependency-groups]` — pip users won't get them.
- Add a `# NOT on PyPI` comment above `[dependency-groups]` as documentation.
- If CI uses both pip and uv steps, add a check: `uv run pytest` not `pytest` directly,
  to ensure uv-managed env is active.
- Mention the uv requirement in README and CONTRIBUTING.

## Related

- `git-workflows/2026-04-01-mkdocs-github-pages-uv-production-pattern.md` — CI commands using `--group docs`
- PEP 735 spec: https://peps.python.org/pep-0735/
- uv docs on dependency groups: https://docs.astral.sh/uv/concepts/projects/#dependency-groups
- PyPI extras (optional-dependencies): https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#optional-dependencies
