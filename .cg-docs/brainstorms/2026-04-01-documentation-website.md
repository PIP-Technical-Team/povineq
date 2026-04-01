---
date: 2026-04-01
title: "Documentation website for povineq"
status: decided
chosen-approach: "MkDocs + Material + mkdocstrings"
tags: [documentation, website, mkdocs, api-reference, tutorials]
---

# Documentation Website for povineq

## Context

The `povineq` package needs a documentation website similar to what `pkgdown`
provides for R packages (e.g., [pipr](https://worldbank.github.io/pipr)). The
project already declares a documentation URL at
`https://pip-technical-team.github.io/povineq/` in `pyproject.toml` but has no
docs site yet.

## Requirements

- **Audience**: General Python users (not R/World Bank-specific). New users who
  want to access the PIP API from Python.
- **Content depth**: Full API reference auto-generated from docstrings, plus
  multiple tutorials/vignettes (Getting Started, Poverty Statistics, Country
  Profiles, Auxiliary Data, etc.).
- **Style**: Follow Python documentation conventions (not mirroring pipr's
  pkgdown structure).
- **Hosting**: GitHub Pages at `pip-technical-team.github.io/povineq/`.
- **Maintenance**: Must be easy to maintain — low config overhead, Markdown-native.

## Approaches Considered

### Approach 1: MkDocs + Material + mkdocstrings (Chosen)

Use MkDocs with the Material for MkDocs theme and the `mkdocstrings-python`
plugin for auto-generated API docs.

**Pros:**
- Markdown-native — all content is `.md`, no RST learning curve
- Material theme is the best-looking Python docs theme today (used by Pydantic,
  FastAPI, Polars, httpx — libraries `povineq` already depends on)
- `mkdocstrings-python` auto-renders docstrings to API reference pages
- `mkdocs-jupyter` plugin can render Jupyter notebooks as tutorial pages
- Dead-simple `mkdocs.yml` config; easy to maintain
- One-command GitHub Pages deploy (`mkdocs gh-deploy`)
- Extremely fast build times

**Cons:**
- Less extensible than Sphinx for highly custom cross-referencing
- No built-in intersphinx-style linking to other projects

**Effort:** Small

### Approach 2: Sphinx + MyST + Furo

Use Sphinx with MyST-Parser (Markdown support) and the Furo theme.

**Pros:**
- Industry standard (CPython, NumPy, pandas)
- Most mature ecosystem with hundreds of extensions
- Intersphinx cross-references
- MyST-Parser allows Markdown

**Cons:**
- More complex configuration (`conf.py` + extensions + templates)
- Steeper learning curve
- Slower builds, more boilerplate

**Effort:** Medium

### Approach 3: Quartodoc (Quarto-based)

Use Quarto with the `quartodoc` extension for API reference generation.

**Pros:**
- Excellent notebook integration
- Cross-language potential (could document pipr + povineq together)
- Good for data science audiences

**Cons:**
- `quartodoc` is less mature — smaller community, fewer examples
- Requires Quarto CLI (not just a Python dependency)
- Less "Pythonic" — unfamiliar to target audience
- GitHub Pages deploy is more manual

**Effort:** Medium

## Decision

**Approach 1: MkDocs + Material + mkdocstrings** was chosen because:

1. Lowest maintenance burden — Markdown-only, minimal config
2. Best visual result out of the box with Material theme
3. Familiar to Python users (same docs style as httpx, pydantic, polars)
4. Easy GitHub Pages deployment via `mkdocs gh-deploy` or GitHub Actions
5. The project is a mid-size API wrapper, not a massive framework — MkDocs is
   the right tool for this scale

## Next Steps

1. Add `docs` optional dependency group to `pyproject.toml`:
   - `mkdocs-material`, `mkdocstrings[python]`, `mkdocs-jupyter`
2. Create `mkdocs.yml` with site name, theme config, nav structure, and
   mkdocstrings plugin
3. Create `docs/` directory with:
   - `index.md` — landing page (adapted from README)
   - `getting-started.md` — installation + first query tutorial
   - `tutorials/` — vignette-style guides (stats, country profiles, auxiliary)
   - `reference/` — auto-generated API reference pages
4. Add a GitHub Actions workflow (`.github/workflows/docs.yml`) to build and
   deploy to GitHub Pages on push to `main`
5. Verify the site renders at `pip-technical-team.github.io/povineq/`
