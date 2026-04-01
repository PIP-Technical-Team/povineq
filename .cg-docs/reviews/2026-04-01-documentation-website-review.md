## Review Report

**Review depth**: thorough  
**Files reviewed**: 8 (`.gitignore`, `pyproject.toml`, `roadmap.json`, `uv.lock`, `.github/workflows/docs.yml`, `docs/**`, `mkdocs.yml`, `docs/gen_ref_pages.py`)  
**Findings**: 0 P1 · 12 P2 · 7 P3

**Fix-triage status (2026-04-01)**: All 19 findings fixed.

---

### P1 — CRITICAL (must fix before merge)

_None._

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-version-control] `.gitignore:12` — `.cg-docs/` is gitignored and will not be committed  
  **Why**: The comment "generated, not part of the package" is incorrect — `.cg-docs/plans/`, `.cg-docs/brainstorms/`, and `.cg-docs/solutions/` are knowledge artifacts that the Compound GPID system expects to accumulate and share with the team. Gitignoring this directory means the plan and brainstorm files created in this session will not be committed.  
  **Fix**: Remove `.cg-docs/` from `.gitignore`. If there are any machine-local files inside, add a nested pattern (e.g., `.cg-docs/**/*.local.md`) instead of excluding the whole directory.

- **[P2.2]** [cg-documentation] `docs/getting-started.md:~130` — `PIPValidationError` caught but not imported  
  **Why**: The error handling example catches `PIPValidationError` in an `except` clause, but the `from povineq import …` statement only imports `PIPAPIError`, `PIPConnectionError`, and `PIPRateLimitError`. Copying this snippet verbatim raises `NameError`.  
  **Fix**:
  ```python
  from povineq import PIPAPIError, PIPConnectionError, PIPRateLimitError, PIPValidationError
  ```

- **[P2.3]** [cg-data-quality] `docs/gen_ref_pages.py:18` — Missing module files skipped silently  
  **Why**: `if not py_path.exists(): continue` produces no signal. If a listed module is renamed, its reference page silently disappears from the built docs with no CI warning.  
  **Fix**: Replace with a warning (or a hard error for CI strictness):
  ```python
  import warnings
  if not py_path.exists():
      warnings.warn(
          f"Listed module {py_path} not found — no reference page generated.",
          stacklevel=1,
      )
      continue
  ```
  For CI hardening, use `raise FileNotFoundError(...)` instead.

- **[P2.4]** [cg-architecture] `docs/gen_ref_pages.py:13` — Hardcoded module list silently omits newly added public modules  
  **Why**: When a new public module is added to `src/povineq/`, nothing alerts the developer to add it to `public_modules`. Documentation coverage degrades invisibly.  
  **Fix**: Add a discovery assertion after the module loop:
  ```python
  existing_public = {p.stem for p in mod_root.glob("[a-z]*.py")}
  documented = set(public_modules)
  undocumented = existing_public - documented
  if undocumented:
      raise ValueError(f"Public modules not in gen_ref_pages.py: {undocumented}. Add them or exclude explicitly.")
  ```

- **[P2.5]** [cg-architecture] `docs/gen_ref_pages.py:22` — Private modules exposed as top-level API reference pages  
  **Why**: Stripping the leading underscore from `_errors`, `_response`, `_cache` and publishing them at `reference/errors.md` etc. implies a stable public contract for internal modules. If these internals change, the docs become misleading and create implicit commitments.  
  **Fix**: Either document only what is re-exported via `__init__.__all__` (remove `internal_public` list), or namespace them under `reference/internal/` to signal they are not part of the stable API:
  ```python
  full_doc_path = Path("reference", "internal", f"{doc_name}.md")
  ```

- **[P2.6]** [cg-architecture] `pyproject.toml:36` — `dev` and `docs` groups pollute the public package extras on PyPI  
  **Why**: Entries under `[project.optional-dependencies]` are published to PyPI. Users will see `pip install povineq[dev]` and `pip install povineq[docs]` as installable extras, polluting the public API surface with build tooling. Only `polars` should be a user-facing extra.  
  **Fix**: Move `dev` and `docs` to `[dependency-groups]` (PEP 735, supported by `uv`):
  ```toml
  [dependency-groups]
  dev = [
      "pytest>=8.0",
      ...
  ]
  docs = [
      "mkdocs-material>=9.5",
      ...
  ]
  ```
  Update CI commands: `uv sync --extra docs` → `uv sync --group docs` (and same for `dev`).

- **[P2.7]** [cg-testing] `.github/workflows/docs.yml` — Build and deploy are coupled in a single step  
  **Why**: `mkdocs gh-deploy --force` combines build + push to `gh-pages`. If the build fails (missing module, malformed docstring), the error is buried in deployment output and it's unclear whether a partial deploy occurred.  
  **Fix**:
  ```yaml
  - name: Build docs
    run: uv run mkdocs build --strict
  - name: Deploy docs
    run: uv run mkdocs gh-deploy --force
  ```
  The `--strict` flag promotes warnings (e.g., broken cross-references) to errors.

- **[P2.8]** [cg-testing] `.github/workflows/ci.yml` — No docs build smoke test in the main CI pipeline  
  **Why**: Documentation build failures will only surface after merge to `main` when the docs workflow runs — too late for PR feedback. A syntax error in `gen_ref_pages.py` or a bad docstring would not be caught during code review.  
  **Fix**: Add a docs build step to the existing `ci.yml`:
  ```yaml
  - name: Build docs (smoke test)
    run: uv run mkdocs build --strict
  ```

- **[P2.9]** [cg-reproducibility] `.github/workflows/docs.yml:15` — `setup-uv` uses `version: "latest"`, not pinned  
  **Why**: The lockfile pins Python dependencies but not the tool reading it. Different uv versions across runs could change resolver behavior, breaking reproducibility.  
  **Fix**: Pin to a specific version:
  ```yaml
  - name: Install uv
    uses: astral-sh/setup-uv@v4
    with:
      version: "0.6.x"   # update to current stable
  ```

- **[P2.10]** [cg-version-control] `.github/workflows/docs.yml` — No concurrency control  
  **Why**: Two rapid pushes to `main` can trigger concurrent deploys. With `--force`, simultaneous `gh-push` calls race and can leave the `gh-pages` branch in an inconsistent state.  
  **Fix**: Add a concurrency group above `jobs:`:
  ```yaml
  concurrency:
    group: deploy-docs
    cancel-in-progress: true
  ```

- **[P2.11]** [cg-architecture] `.github/workflows/docs.yml:4` — Triggers on every push to `main`, no path filter  
  **Why**: Any commit — a one-line test fix, a bump in `uv.lock` — triggers a full docs rebuild and deployment, wasting CI minutes.  
  **Fix**:
  ```yaml
  on:
    push:
      branches: [main]
      paths:
        - "docs/**"
        - "mkdocs.yml"
        - "src/povineq/**/*.py"
        - "pyproject.toml"
    workflow_dispatch:
  ```

- **[P2.12]** [cg-documentation] `docs/index.md`, `docs/getting-started.md` — `pip install povineq` may fail if package is not yet on PyPI  
  **Why**: The package is at version `0.1.0` with classifier `Development Status :: 3 - Alpha`. If it has not been published to PyPI yet, the installation instructions will produce an unhelpful "package not found" error for users who discover the docs.  
  **Fix**: Add a temporary notice until the package is live:
  ```markdown
  !!! note "Pre-release"
      `povineq` is in active development. If `pip install povineq` fails,
      install directly from source:
      `pip install git+https://github.com/PIP-Technical-Team/povineq.git`
  ```
  Remove this note once the first release is published on PyPI.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `docs/gen_ref_pages.py:40` — If/elif/else metadata computation should be a helper function  
  **Why**: The three-branch `(doc_name, identifier, title)` logic is embedded in the main loop, making it harder to read and test.  
  **Fix**: Extract to `def _module_metadata(mod_name: str) -> tuple[str, str, str]: ...`

- **[P3.2]** [cg-code-quality] `docs/gen_ref_pages.py:19` — Package name `"povineq"` is a magic string  
  **Why**: The name appears twice (`mod_root = Path("src", "povineq")` and in the `__init__` identifier). A rename requires two edits.  
  **Fix**: `PACKAGE_NAME = "povineq"` at module top; use everywhere.

- **[P3.3]** [cg-data-quality] `docs/gen_ref_pages.py:28` — `lstrip("_")` strips all leading underscores  
  **Why**: `lstrip("_")` removes every `_` prefix; `__foo` would produce `foo`. Use `str.removeprefix("_")` (Python 3.9+) to strip exactly one.  
  **Fix**: `doc_name = mod_name.removeprefix("_")`

- **[P3.4]** [cg-architecture] `docs/gen_ref_pages.py` — Build script in `docs/` root, not `docs/scripts/`  
  **Why**: A Python script mixed in with Markdown content is a minor organization smell.  
  **Fix**: Move to `docs/scripts/gen_ref_pages.py`; update `mkdocs.yml`:
  ```yaml
  - gen-files:
      scripts:
        - docs/scripts/gen_ref_pages.py
  ```

- **[P3.5]** [cg-architecture] `docs/gen_ref_pages.py:28` — Underscore-stripping creates a latent name collision  
  **Why**: `_cache` → `cache.md`, `_errors` → `errors.md`. If a public `cache.py` or `errors.py` is ever added, the second file silently overwrites the first with no error.  
  **Fix**: Namespace internal pages under `reference/internal/` or use a distinguishing prefix.

- **[P3.6]** [cg-architecture] `mkdocs.yml` — No CHANGELOG in navigation  
  **Why**: A published package with a `Documentation` URL in PyPI metadata should surface release notes prominently.  
  **Fix**: Add `CHANGELOG.md` (at minimum a stub pointing to GitHub Releases) and add to nav:
  ```yaml
  - Changelog: changelog.md
  ```

- **[P3.7]** [cg-code-quality] `docs/gen_ref_pages.py:47` — Variable name `fd` is opaque  
  **Why**: `fd` conventionally denotes a low-level file descriptor integer, not a text file wrapper.  
  **Fix**: Rename to `out` or `md_file`.

---

### ✅ Passed

- **cg-performance**: No performance issues — trivial build loop with no nested I/O or memory concerns.
- **cg-documentation**: Google-style docstrings consistently applied across all source modules; matches `mkdocs.yml` `docstring_style: google` setting.
- **cg-documentation**: `reference/errors.md` link in `getting-started.md` is valid — `gen_ref_pages.py` generates it from `_errors.py`.
- **cg-version-control**: No secrets or credentials exposed in any new files.
- **cg-version-control**: `site/` correctly added to `.gitignore`.
- **cg-version-control**: `uv.lock` updated and committed with new docs dependencies.
- **cg-reproducibility**: `uv sync` correctly reads lockfile; module order is deterministic (explicit list); `Path()` usage is cross-platform.
- **cg-learnings-researcher**: Implementation correctly follows the brainstorm and plan artifacts in `.cg-docs/`. No conflicting past decisions found.
