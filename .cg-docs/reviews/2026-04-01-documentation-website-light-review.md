## Review Report

**Review depth**: light
**Files reviewed**: 7 (`.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.gitignore`, `pyproject.toml`, `roadmap.json`, `mkdocs.yml`, `docs/`)
**Findings**: 0 P1 · 5 P2 · 3 P3

---

### P1 — CRITICAL (must fix before merge)

_None._

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/workflows/docs.yml:41` — `mkdocs gh-deploy --force` bypasses safety checks
  **Why**: The `--force` flag overwrites the `gh-pages` branch unconditionally, which can silently overwrite hotfixes or manual changes made to the branch between CI runs.
  **Fix**: Remove `--force`; the default `gh-deploy` without `--force` still works correctly for a clean Pages branch driven entirely by CI.

- **[P2.2]** [cg-code-quality] `.gitignore` — `docs/reference/` not excluded
  **Why**: `mkdocs-gen-files` generates `docs/reference/*.md` at build time. If these are ever accidentally written to disk during local development, Git will start tracking them as source files.
  **Fix**: Add `docs/reference/` to `.gitignore`.

- **[P2.3]** [cg-testing] `.github/workflows/docs.yml` — No post-build validation of generated docs structure
  **Why**: `mkdocs build --strict` catches broken internal links but does not verify that `gen_ref_pages.py` produced all expected reference files. A broken plugin would silently emit an empty `docs/reference/`.
  **Fix**: Add a post-build step, e.g. `python -c "import pathlib; assert list(pathlib.Path('site/reference').glob('*.html')), 'Reference pages missing'"`.

- **[P2.4]** [cg-testing] `pyproject.toml:36-45` — `[dependency-groups]` (PEP 735) requires `uv`; plain `pip` cannot install the `docs` group
  **Why**: `pip install .[docs]` (standard PEP 517 path) silently ignores `[dependency-groups]`, so contributors using plain pip cannot build the docs. The `pyproject.toml` advertises Python 3.10+ support, implying standard tooling should work.
  **Fix**: Either move docs dependencies to `[project.optional-dependencies]` (e.g. `docs = [...]`) for pip compatibility, or clearly document in README/CONTRIBUTING that `uv` is required for docs.

- **[P2.5]** [cg-code-quality + cg-testing] `.github/workflows/ci.yml:43` — Docs build smoke-test runs only on Python 3.12 in matrix
  **Why**: The matrix covers 3.10, 3.11, 3.12, but `gen_ref_pages.py` and the mkdocstrings introspection path are only exercised on 3.12. A Python-version-specific import failure in the docs build would go undetected on 3.10/3.11.
  **Fix**: Extract the docs smoke-test into a dedicated job that runs once on a single explicit stable version (e.g. `python-version: "3.12"`) to make the intent explicit, or add a comment: `# docs build intentionally runs only on latest Python`.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/workflows/docs.yml:27` — `uv-version: "0.6.x"` is an unpinned range
  **Why**: Range pins allow minor-version drift between CI runs, reducing reproducibility. `ci.yml` uses an exact pin for comparison.
  **Fix**: Pin to an exact version, e.g. `uv-version: "0.6.4"` (check astral-sh/setup-uv for the current recommended version).

- **[P3.2]** [cg-code-quality] `mkdocs.yml:34` — `paths: [src]` uses unquoted flow sequence
  **Why**: mkdocstrings documentation uses quoted strings (`paths: ["src"]`); unquoted flow sequences can cause YAML parser edge-case issues in some environments.
  **Fix**: Change to `paths: ["src"]`.

- **[P3.3]** [cg-testing] `mkdocs.yml:39` — `docstring_style: google` enforced at build time only; no linter in CI
  **Why**: Docstring style violations only surface when building docs, creating a slow feedback loop for contributors.
  **Fix**: Add `pydocstyle --convention=google` or `ruff select D` to the CI lint step so docstring issues are caught on every push.

---

### ✅ Passed

- **cg-code-quality**: `hishel` removal verified safe by cg-testing (no imports in `src/`)
- **cg-code-quality**: GitHub Actions versions are current (`checkout@v4`, `setup-python@v5`, `setup-uv@v4`)
- **cg-code-quality**: CI matrix configuration (`fail-fast: false`, 3.10–3.12) is sound
- **cg-code-quality**: `pyproject.toml` dependency version pins are appropriate (`>=0.5`, etc.)
- **cg-code-quality**: MkDocs plugin configuration structure is valid
- **cg-testing**: `mkdocs build --strict` used in `docs.yml` (catches broken references)
- **cg-testing**: Test suite configuration (`pytest`, coverage at 85%, `-m "not online"` filter) is correct
- **cg-testing**: All existing test files are unmodified and intact
