---
date: 2026-04-01
title: "Production-ready MkDocs + GitHub Pages + uv CI/CD workflow"
category: "git-workflows"
language: "Python"
tags: [mkdocs, github-pages, uv, ci-cd, github-actions, documentation, concurrency, mkdocstrings, material]
root-cause: "Default MkDocs gh-deploy setup has several reliability and reproducibility issues: no concurrency guard, no path filter, --force overwrites, build/deploy coupled, uv unpinned, and no PR smoke test."
severity: "P2"
---

# Production-Ready MkDocs + GitHub Pages + uv CI/CD Workflow

## Problem

A minimal `mkdocs gh-deploy` workflow works locally but has several reliability
problems in CI:

1. **Race condition**: Two rapid pushes trigger concurrent deploys; both run
   `--force` simultaneously and can corrupt `gh-pages`.
2. **Unnecessary builds**: Any commit (test fix, lock file bump) triggers a full
   docs rebuild, wasting CI minutes.
3. **Hidden build failures**: `gh-deploy` combines build + push; if the build
   fails, it is unclear whether a partial deploy occurred.
4. **Unpinned tooling**: `uv-version: "latest"` or `"0.6.x"` allows silent
   minor-version drift between CI runs.
5. **No PR feedback**: Documentation build errors only surface after merge when
   the docs workflow runs — too late during code review.
6. **Generated files tracked by git**: `mkdocs-gen-files` can write `docs/reference/`
   to disk during local dev; if not gitignored, those files get committed.

## Root Cause

MkDocs beginner guides show the simplest possible workflow (`mkdocs gh-deploy --force`
in one step) which is not designed for production. Several independent safeguards
must be added explicitly.

## Solution

### `.github/workflows/docs.yml` — Deploy workflow

```yaml
name: Deploy docs

on:
  push:
    branches: [main]
    paths:                          # Only rebuild when docs-related files change
      - "docs/**"
      - "mkdocs.yml"
      - "src/povineq/**/*.py"
      - "pyproject.toml"
  workflow_dispatch:               # Allow manual triggering

concurrency:                       # Prevent race conditions on concurrent pushes
  group: deploy-docs
  cancel-in-progress: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0           # Required for git-revision-date plugin

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "0.6.4"        # Pin exact version, not "latest" or "0.6.x"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install docs dependencies
        run: uv sync --group docs

      - name: Build docs                    # Separate build step with strict mode
        run: uv run mkdocs build --strict   # --strict promotes warnings to errors

      - name: Deploy docs
        run: uv run mkdocs gh-deploy --force
```

### `.github/workflows/ci.yml` — Smoke test in PR pipeline

```yaml
# Add this step to the existing test matrix job (runs on all Python versions OR
# extract to a dedicated job on a single stable version)
- name: Build docs (smoke test)
  run: uv sync --group docs && uv run mkdocs build --strict
```

### `.gitignore`

```gitignore
# MkDocs build output
site/

# mkdocs-gen-files generated reference stubs (build-time only)
docs/reference/
```

### `pyproject.toml` — Separate user extras from dev/docs tooling

```toml
# User-facing extras (published to PyPI — keep minimal)
[project.optional-dependencies]
polars = ["polars>=0.20"]

# Dev/docs tooling (uv-only, NOT published to PyPI)
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "httpx>=0.27",
    "respx>=0.21",
]
docs = [
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.24",
    "mkdocs-gen-files>=0.5",
    "mkdocs-literate-nav>=0.6",
    "mkdocs-section-index>=0.3",
]
```

**CI install commands:**
- Tests: `uv sync --group dev`
- Docs: `uv sync --group docs`
- Both: `uv sync --group dev --group docs`

## Prevention

- Always split `mkdocs build --strict` and `mkdocs gh-deploy` into separate steps.
- Always add `concurrency:` group to any deploy workflow that uses `--force`.
- Always add `paths:` filter to docs workflows to avoid rebuilding on unrelated commits.
- Pin exact `uv-version` (not "latest" or semver range) for reproducibility.
- Add a docs build step to `ci.yml` to get PR-time feedback, not just post-merge.
- Add `docs/reference/` to `.gitignore` if using `mkdocs-gen-files`.
- Keep `[dependency-groups]` for dev/docs (uv-only, not on PyPI) and
  `[project.optional-dependencies]` only for user-facing extras.

## Related

- `build-errors/2026-04-01-pep735-dependency-groups-pip-incompatible.md` — why dev/docs should be in `[dependency-groups]`, not `[project.optional-dependencies]`
- MkDocs deployment docs: https://www.mkdocs.org/user-guide/deploying-your-docs/
- astral-sh/setup-uv: https://github.com/astral-sh/setup-uv
- GitHub Actions concurrency: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/using-concurrency
