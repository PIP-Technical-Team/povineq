---
date: 2026-04-01
title: "Documentation website with MkDocs + Material"
status: active
brainstorm: ".cg-docs/brainstorms/2026-04-01-documentation-website.md"
language: "Python"
estimated-effort: "medium"
tags: [documentation, mkdocs, api-reference, tutorials, github-pages]
---

# Plan: Documentation Website with MkDocs + Material

## Objective

Build and deploy a documentation website for `povineq` at
`pip-technical-team.github.io/povineq/` using MkDocs + Material for MkDocs +
mkdocstrings. The site will serve as the primary documentation entry point for
Python users who want to query the World Bank PIP API, providing auto-generated
API reference pages plus hand-written tutorials.

## Context

- **Brainstorm**: The team decided on MkDocs + Material + mkdocstrings as the
  documentation stack (see brainstorm).
- **Existing code**: All public functions already have Google-style docstrings
  with Args, Returns, Raises, and Example sections — ready for mkdocstrings to
  consume.
- **Public API surface**: 4 public modules (`stats`, `auxiliary`,
  `country_profiles`, `info`) plus supporting types (`_errors`, `_response`,
  `_cache`). ~30 exported symbols in `__init__.py`.
- **CI**: GitHub Actions with uv already exists at `.github/workflows/ci.yml`.
- **Hosting**: `pyproject.toml` already declares the docs URL as
  `https://pip-technical-team.github.io/povineq/`.
- **Audience**: General Python users, not R/World Bank-specific. Docs should
  follow Python conventions and be beginner-friendly.

## Implementation Steps

### 1. Add `docs` dependency group to `pyproject.toml`

- **Files**: `pyproject.toml`
- **Details**: Add a new `[project.optional-dependencies]` group called `docs`:
  ```toml
  docs = [
      "mkdocs-material>=9.5",
      "mkdocstrings[python]>=0.25",
      "mkdocs-gen-files>=0.5",
      "mkdocs-literate-nav>=0.6",
      "mkdocs-section-index>=0.3",
  ]
  ```
  - `mkdocs-material`: theme
  - `mkdocstrings[python]`: auto-generates API reference from docstrings
  - `mkdocs-gen-files`: programmatically generates reference pages at build time
  - `mkdocs-literate-nav`: allows nav to be defined in a SUMMARY.md file
  - `mkdocs-section-index`: makes section index pages clickable
- **Tests**: `uv sync --extra docs` succeeds without errors.
- **Acceptance criteria**: All docs dependencies install cleanly.

### 2. Create `mkdocs.yml` configuration

- **Files**: `mkdocs.yml` (project root)
- **Details**:
  ```yaml
  site_name: povineq
  site_url: https://pip-technical-team.github.io/povineq/
  site_description: Python wrapper for the World Bank PIP API
  repo_url: https://github.com/PIP-Technical-Team/povineq
  repo_name: PIP-Technical-Team/povineq

  theme:
    name: material
    palette:
      - scheme: default
        primary: indigo
        accent: indigo
        toggle:
          icon: material/brightness-7
          name: Switch to dark mode
      - scheme: slate
        primary: indigo
        accent: indigo
        toggle:
          icon: material/brightness-4
          name: Switch to light mode
    features:
      - navigation.tabs
      - navigation.sections
      - navigation.expand
      - navigation.top
      - search.suggest
      - search.highlight
      - content.code.copy

  plugins:
    - search
    - mkdocstrings:
        handlers:
          python:
            paths: [src]
            options:
              docstring_style: google
              show_source: true
              show_root_heading: true
              show_root_full_path: false
              members_order: source
              merge_init_into_class: true
              show_if_no_docstring: false
    - gen-files:
        scripts:
          - docs/gen_ref_pages.py
    - literate-nav:
        nav_file: SUMMARY.md
    - section-index

  nav:
    - Home: index.md
    - Getting Started: getting-started.md
    - Tutorials:
        - Poverty Statistics: tutorials/poverty-statistics.md
        - Country Profiles: tutorials/country-profiles.md
        - Auxiliary Data: tutorials/auxiliary-data.md
        - Caching and Performance: tutorials/caching.md
    - API Reference: reference/

  markdown_extensions:
    - admonition
    - pymdownx.details
    - pymdownx.superfences
    - pymdownx.highlight:
        anchor_linenums: true
    - pymdownx.inlinehilite
    - pymdownx.snippets
    - pymdownx.tabbed:
        alternate_style: true
    - toc:
        permalink: true
    - attr_list
    - md_in_html
  ```
- **Tests**: `uv run mkdocs build --strict` succeeds without warnings.
- **Acceptance criteria**: Config is valid and produces a navigable site.

### 3. Create `docs/` content pages

- **Files**:
  - `docs/index.md` — Landing page
  - `docs/getting-started.md` — Installation, first query, basic patterns
  - `docs/tutorials/poverty-statistics.md` — Working with `get_stats`, `get_wb`, `get_agg`
  - `docs/tutorials/country-profiles.md` — Working with `get_cp`, `get_cp_ki`, `unnest_ki`
  - `docs/tutorials/auxiliary-data.md` — Working with `get_aux`, convenience wrappers, in-memory store
  - `docs/tutorials/caching.md` — Cache management, `delete_cache`, `get_cache_info`
- **Details**:
  - `index.md`: Adapted from README.md. Overview of the package, feature list,
    quick install, and links to Getting Started / API Reference.
  - `getting-started.md`: Step-by-step: install, import, first `get_stats()`
    call, interpreting the DataFrame, switching to polars, using `simplify=False`,
    checking the API, error handling basics.
  - Each tutorial page: introduces the module, shows common usage patterns with
    code examples, covers key parameters, documents edge cases and gotchas, and
    links to the relevant API reference pages via `::: povineq.func` cross-refs.
- **Tests**: All internal links resolve (no broken cross-references in strict build).
- **Acceptance criteria**: Each page renders correctly with proper formatting.

### 4. Create API reference auto-generation script

- **Files**:
  - `docs/gen_ref_pages.py` — Script consumed by `mkdocs-gen-files` at build time
- **Details**:
  The script programmatically creates one reference page per public module:
  ```python
  # docs/gen_ref_pages.py
  """Generate API reference pages for mkdocstrings."""
  from pathlib import Path
  import mkdocs_gen_files

  nav = mkdocs_gen_files.Nav()
  mod_root = Path("src", "povineq")

  # Public modules to document
  public_modules = [
      "__init__",
      "stats",
      "country_profiles",
      "auxiliary",
      "info",
  ]
  # Internal modules that export public types
  internal_public = [
      "_errors",
      "_response",
      "_cache",
  ]

  for mod_name in public_modules + internal_public:
      py_path = mod_root / f"{mod_name}.py"
      if not py_path.exists():
          continue

      # Build the doc filename
      if mod_name == "__init__":
          doc_name = "index"
          identifier = "povineq"
          title = "povineq (top-level)"
      elif mod_name.startswith("_"):
          doc_name = mod_name.lstrip("_")
          identifier = f"povineq.{mod_name}"
          title = doc_name.replace("_", " ").title()
      else:
          doc_name = mod_name
          identifier = f"povineq.{mod_name}"
          title = mod_name.replace("_", " ").title()

      doc_path = Path("reference", f"{doc_name}.md")
      full_doc_path = Path("reference", f"{doc_name}.md")

      with mkdocs_gen_files.open(full_doc_path, "w") as fd:
          fd.write(f"# {title}\n\n::: {identifier}\n")

      mkdocs_gen_files.set_edit_path(full_doc_path, py_path)
      nav[doc_name] = f"{doc_name}.md"

  # Write SUMMARY.md for literate-nav
  with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
      nav_file.writelines(nav.build_literate_nav())
  ```
  This auto-generates:
  - `reference/index.md` → `povineq` top-level (all exports)
  - `reference/stats.md` → `povineq.stats`
  - `reference/country_profiles.md` → `povineq.country_profiles`
  - `reference/auxiliary.md` → `povineq.auxiliary`
  - `reference/info.md` → `povineq.info`
  - `reference/errors.md` → `povineq._errors`
  - `reference/response.md` → `povineq._response`
  - `reference/cache.md` → `povineq._cache`
- **Tests**: `uv run mkdocs build --strict` generates all reference pages
  without warnings.
- **Acceptance criteria**: Every public function and class has an API reference
  entry with rendered docstring, parameter table, and return type.

### 5. Add GitHub Actions workflow for docs deployment

- **Files**: `.github/workflows/docs.yml`
- **Details**:
  ```yaml
  name: Docs

  on:
    push:
      branches: [main]
    workflow_dispatch:

  permissions:
    contents: write

  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v4
          with:
            version: "latest"

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: "3.12"

        - name: Install dependencies
          run: uv sync --extra docs

        - name: Build and deploy
          run: uv run mkdocs gh-deploy --force
  ```
- **Tests**: Workflow YAML is valid (no syntax errors). Docs build succeeds in CI.
- **Acceptance criteria**: Push to `main` triggers docs build and deploys to
  the `gh-pages` branch, visible at
  `pip-technical-team.github.io/povineq/`.

### 6. Add `docs/` to `.gitignore` exclusions and verify local build

- **Files**: `.gitignore` (if needed)
- **Details**:
  - Ensure `site/` (MkDocs build output) is gitignored.
  - Verify local workflow:
    - `uv sync --extra docs`
    - `uv run mkdocs serve` → opens at `http://localhost:8000`
    - `uv run mkdocs build --strict` → no warnings
- **Tests**: Local dev server starts and all pages render.
- **Acceptance criteria**: Contributors can preview docs locally with one command.

## Testing Strategy

- **Build validation**: `uv run mkdocs build --strict` must produce zero
  warnings. This catches broken cross-references, missing pages, and
  docstring parsing errors.
- **Link checking**: Enable the `htmlproofer` or manual review to verify
  all internal and external links resolve.
- **Visual review**: Preview locally via `mkdocs serve` before merging.
- **CI gating**: The docs workflow runs on every push to `main`, ensuring
  the docs site stays in sync with the code.

## Documentation Checklist

- [x] Function documentation (docstrings) — already complete in all modules
- [ ] Landing page (`docs/index.md`)
- [ ] Getting Started tutorial
- [ ] Tutorial: Poverty Statistics
- [ ] Tutorial: Country Profiles
- [ ] Tutorial: Auxiliary Data
- [ ] Tutorial: Caching and Performance
- [ ] API reference pages (auto-generated)
- [ ] README update (link to docs site) — already links to correct URL

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| mkdocstrings fails on complex type hints | Use `show_signature_annotations: false` as fallback |
| `mkdocs-gen-files` breaks with src layout | Explicit `paths: [src]` in mkdocstrings handler config |
| GitHub Pages not enabled on repo | Requires one-time repo settings change: Settings → Pages → Source → `gh-pages` branch |
| Large API responses in tutorial code blocks | Use `>>> # doctest: +SKIP` or truncated output snippets |

## Out of Scope

- Jupyter notebook rendering in tutorials (future enhancement — use
  `mkdocs-jupyter` later if needed)
- Versioned documentation (multiple package versions) — not needed until v1.0
  stable release
- Custom domain (staying with `github.io` subdomain for now)
- API changelog / release notes page (tracked in NEWS.md / GitHub Releases)
- Translations / i18n
