## Review Report (Light — 2026-04-01)

**Review depth**: thorough  
**Files reviewed**: 34  
**Findings**: 2 P1 · 25 P2 · 12 P3  
**Date**: 2026-04-01  
**Agents**: cg-code-quality · cg-testing · cg-documentation · cg-version-control · cg-reproducibility · cg-performance · cg-architecture · cg-data-quality · cg-learnings-researcher

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `src/povineq/utils.py:44` — `hasattr(val, "__len__")` accepts strings as valid decile data  
  **Why**: A string in the `deciles` column passes this guard — `"hello".__len__()` is valid — so `val[i]` returns individual characters and decile columns are silently filled with characters instead of floats. Silent data corruption.  
  **Fix**: Replace `hasattr(val, "__len__")` with `isinstance(val, (list, tuple))`

- **[P1.2]** [cg-data-quality] `src/povineq/utils.py:39-57` — Non-uniform decile counts across rows silently produce None-padded or truncated output  
  **Why**: Column count is inferred from the first non-null row only. Rows with a different list length get `None` for extra columns or have values silently truncated — corrupt output with no error or warning.  
  **Fix**: Validate that all non-null rows have the same decile count; raise `ValueError` on mismatch

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality, cg-architecture, cg-reproducibility, cg-documentation] `src/povineq/_cache.py:36,41` — `print()` used instead of loguru logger  
  **Why**: Violates the project's explicit loguru requirement; cannot be suppressed or redirected by log level; inconsistent with every other module.  
  **Fix**: Add `from loguru import logger`; replace `print(...)` with `logger.info(...)`

- **[P2.2]** [cg-code-quality] `src/povineq/auxiliary.py:159,161` — `print()` used in `display_aux()`  
  **Why**: Same as P2.1; loguru is already imported in this module.  
  **Fix**: Replace `print("Available auxiliary tables:")` / `print(f"  - {t}")` with `logger.info(...)` calls

- **[P2.3]** [cg-code-quality] `src/povineq/_request.py:39,86,120` — Bare `except Exception:` clauses  
  **Why**: Catches all exceptions including `KeyboardInterrupt`, `SystemExit`, and programming errors; masks bugs and makes debugging extremely difficult.  
  **Fix**: Line 39: catch `(json.JSONDecodeError, AttributeError, TypeError, KeyError)`; line 86: `(json.JSONDecodeError, ValueError, KeyError, AttributeError, TypeError)`; line 120: add `logger.exception(...)` before return

- **[P2.4]** [cg-code-quality, cg-data-quality] `src/povineq/_response.py:75,83` — Bare `except Exception:` in `_parse_json()`  
  **Why**: Schema normalization failures are swallowed; caller may receive a single-cell DataFrame with the entire dict as one value, with no warning.  
  **Fix**: Catch `(json.JSONDecodeError, ValueError)`; add `logger.warning("Could not normalize response, using raw: ...")` before the fallback

- **[P2.5]** [cg-code-quality] Multiple files — `format` parameter name shadows Python builtin  
  **Why**: Shadowing `format` (builtin) in function signatures is flagged by linters and can confuse readers. Affects `stats.py:33`, `auxiliary.py:24,122,194+` (13 wrapper functions), `country_profiles.py:27`, `_validation.py`.  
  **Fix**: Rename to `output_format` or `fmt` throughout (use find-and-replace carefully to avoid breaking callers)

- **[P2.6]** [cg-code-quality] `tests/test_cache.py:5,9,36`, `tests/test_client.py:5,6`, `tests/test_request.py:5,6,10` — Unused imports and arguments  
  **Why**: Dead imports add noise, hide real issues in linting output, and slow test collection.  
  **Fix**: Remove `import os`, `from unittest.mock import patch` (where unused), `PIPRateLimitError` from import, and `capsys` from `test_deletes_files` signature

- **[P2.7]** [cg-architecture, cg-performance] `src/povineq/_request.py:116` — New `httpx.Client` instantiated inside the retry loop on every API call  
  **Why**: Every API call creates a fresh `httpx.Client` + `FileStorage` + `CacheTransport` — forcing a new TLS handshake/TCP connect each time. Clients are never closed, leaking file descriptors and connection-pool threads. Defeats the entire point of connection pooling.  
  **Fix**: Move `client = get_client(server)` before the retry loop; use it as a context manager or close in `finally`

- **[P2.8]** [cg-performance] `src/povineq/_response.py:49-51` — Arrow → pandas → polars double conversion  
  **Why**: `_parse_arrow` always calls `table.to_pandas()`, then `_to_target_type` calls `pl.from_pandas(df)` for polars — routing through a full numpy copy twice instead of going Arrow → polars directly (which is zero-copy in most cases).  
  **Fix**: Return `pa.Table` from `_parse_arrow`; in `_to_target_type`, use `pl.from_arrow(data)` for polars path

- **[P2.9]** [cg-architecture] `src/povineq/__init__.py:102` and `pyproject.toml:7` — `__version__` hardcoded in two places  
  **Why**: Version drift guaranteed when one is bumped without the other.  
  **Fix**: Replace with `from importlib.metadata import version; __version__ = version("povineq")` in `__init__.py`

- **[P2.10]** [cg-architecture, cg-learnings-researcher] `src/povineq/stats.py:175-177` — Dead `_WbParams` inner class defined but never used  
  **Why**: `get_wb()` defines `class _WbParams(_BaseParams): pass` then immediately builds query dict manually, bypassing it entirely. Dead code + maintenance trap — readers assume the class drives the logic.  
  **Fix**: Remove the dead class and its `_BaseParams` import, or refactor `get_wb()` to actually use a pydantic model like all other endpoints

- **[P2.11]** [cg-architecture, cg-code-quality] `src/povineq/auxiliary.py:221-550` — 13 near-identical thin wrapper functions  
  **Why**: `get_countries`, `get_regions`, `get_cpi`, `get_gdp`, `get_dictionary`, `get_incgrp_coverage`, `get_interpolated_means`, `get_hfce`, `get_pop`, `get_pop_region`, `get_ppp`, `get_region_coverage`, `get_survey_means` are structurally identical (each calls `get_aux(table="X", ...)` with the same 8 params). Adding a new table requires adding a new function + `__init__.py` export. ~170 duplicate lines.  
  **Fix**: Introduce a factory: `_make_aux_getter(table: str) -> Callable`; assign `get_countries = _make_aux_getter("countries")` etc.

- **[P2.12]** [cg-data-quality] `src/povineq/_request.py:102` — Only `httpx.ConnectError` caught; other network exceptions leak as raw httpx types  
  **Why**: `httpx.TimeoutException`, `httpx.ReadTimeout`, `httpx.NetworkError`, `httpx.RemoteProtocolError` all propagate unhandled, breaking the typed `PIPConnectionError` contract.  
  **Fix**: Catch `httpx.RequestError` (base class for all transport-level errors) and wrap in `PIPConnectionError`

- **[P2.13]** [cg-data-quality] `src/povineq/_validation.py:97-98` — `fill_gaps` / `nowcast` set to `None` with `# type: ignore` to bypass `bool` type  
  **Why**: Relies on implicit contract that `to_query_params()` drops `None` values; if that changes, `"None"` is sent to the API silently.  
  **Fix**: Declare fields as `bool | None` in `StatsParams`, remove `# type: ignore`

- **[P2.14]** [cg-data-quality] `src/povineq/auxiliary.py:109` — `assign_tb=True` silently no-ops when `simplify=False`  
  **Why**: When `assign_tb=True, simplify=False`, `rt` is a `PIPResponse`, not a `pd.DataFrame`, so `isinstance(rt, pd.DataFrame)` is `False` — the table is never stored, the function returns the response object, and the caller has no indication storage failed.  
  **Fix**: Add `raise ValueError("assign_tb requires simplify=True")` or `logger.warning(...)` when both conditions can't be satisfied together

- **[P2.15]** [cg-data-quality] `src/povineq/country_profiles.py:~232` — Cross-join fallback in `unnest_ki` silently creates spurious rows  
  **Why**: `result.merge(df_part, how="cross")` produces the full Cartesian product when no common merge keys exist — silently creating tens of thousands of spurious rows.  
  **Fix**: Raise `ValueError` or emit `logger.warning()` instead of silently cross-joining when common columns are missing

- **[P2.16]** [cg-testing] `tests/test_request.py` — `ConnectError` path in `build_and_execute()` never exercised  
  **Why**: The `PIPConnectionError` fast path exists but is completely untested; regressions would be undetected.  
  **Fix**: Add test with patched `httpx.Client.get()` raising `httpx.ConnectError`; verify `PIPConnectionError` is raised

- **[P2.17]** [cg-testing] `tests/test_response.py` — `_to_target_type()` and `_apply_post_processing()` not directly tested; empty responses not covered  
  **Why**: Uncovered helpers can regress silently; empty Arrow/CSV/JSON inputs are realistic edge cases from the API.  
  **Fix**: Add unit tests for each function in isolation; add empty-response parametrized tests

- **[P2.18]** [cg-testing] `tests/test_validation.py` — Boundary values for numeric params untested; `subgroup` case-sensitivity untested  
  **Why**: `povline=-1.0`, `popshare=1.5`, `ppp_version=0`, `subgroup="WB_REGIONS"` (uppercase) are all realistic user mistakes that should be caught.  
  **Fix**: Add `@pytest.mark.parametrize` tests for each invalid value

- **[P2.19]** [cg-version-control] `.gitignore` — `.cg-docs/` directory not gitignored  
  **Why**: `.cg-docs/` contains generated knowledge artifacts that should not be committed; it is currently being tracked.  
  **Fix**: Add `.cg-docs/` to `.gitignore`

- **[P2.20]** [cg-reproducibility, cg-version-control, cg-architecture] project root — No `uv.lock` committed  
  **Why**: Loose version constraints (`httpx>=0.27`, `pydantic>=2.0`, etc.) mean different machines resolve to different versions; CI builds are not reproducible.  
  **Fix**: Run `uv lock` and commit `uv.lock`

- **[P2.21]** [cg-reproducibility] project root — No `.python-version` file  
  **Why**: Without it, tools like `uv`, `pyenv`, and `mise` cannot pin the exact Python version across environments.  
  **Fix**: Create `.python-version` with a specific patch version (e.g., `3.10.14`)

- **[P2.22]** [cg-reproducibility] `.github/workflows/` — No CI workflow found  
  **Why**: Tests are never run automatically; regressions won't be caught until a developer runs them manually.  
  **Fix**: Create `.github/workflows/ci.yml` that uses `uv sync` + `uv run pytest` across Python 3.10–3.12

- **[P2.23]** [cg-documentation] `README.md` — Extremely minimal (only title + one-line description)  
  **Why**: Users cannot install, configure, or use the package from the README alone. This is a publishable package.  
  **Fix**: Expand README with: Installation, Quick Start, Usage Examples, API Reference overview, Contributing

- **[P2.24]** [cg-documentation] `src/povineq/auxiliary.py:206+` — Auxiliary wrapper functions lack `Args` docstring sections  
  **Why**: `get_regions()`, `get_cpi()`, etc. expose the same 8 parameters as `get_aux()` but none document them; new users have no way to discover valid inputs.  
  **Fix**: Add `Args:` section (can be shared via a module-level docstring template or copy from `get_aux()`)

- **[P2.25]** [cg-documentation] `src/povineq/country_profiles.py:152-220` — `unnest_ki()` complex merge logic has no inline explanation  
  **Why**: The function uses multiple join strategies + deduplication in a non-obvious order; future maintainers cannot understand it without running it.  
  **Fix**: Add inline comments explaining the merge strategy, deduplication, and why cross-join is used as a fallback

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-performance] `src/povineq/utils.py:46-62` — Row-by-row Python loop for decile unpacking  
  **Why**: 10× slower than vectorized equivalent for full country×year datasets.  
  **Fix**: Replace loop with `pd.DataFrame(df["deciles"].tolist(), index=df.index).rename(columns=lambda i: f"decile{i+1}")`

- **[P3.2]** [cg-performance] `src/povineq/utils.py:57` — Redundant `.copy()` after `.drop()`  
  **Why**: `.drop(columns=...)` already returns a new DataFrame; `.copy()` allocates a second full copy for no benefit.  
  **Fix**: Remove `.copy()`: `result = df.drop(columns=["deciles"])`

- **[P3.3]** [cg-performance] `src/povineq/country_profiles.py:124-130` — JSON response deserialized twice in `get_cp_ki`  
  **Why**: `parse_response(simplify=False)` deserializes `response.text` to a DataFrame that is immediately discarded, then `json.loads(response.text)` parses it again.  
  **Fix**: Call `response.json()` once, pass the dict directly to `unnest_ki()`

- **[P3.4]** [cg-performance] `src/povineq/_cache.py:10-13` — `mkdir` syscall on every request  
  **Why**: `_cache_dir()` is called from `get_client()` on every API call; it issues a `stat`/`mkdir` syscall even when the directory already exists.  
  **Fix**: Decorate `_cache_dir()` with `@functools.lru_cache(maxsize=1)`

- **[P3.5]** [cg-architecture] `src/povineq/country_profiles.py:~135` — `import json` inside function body  
  **Why**: `json` is a stdlib module; late imports inside functions are reserved for optional heavy dependencies (like polars). Obscures module dependencies.  
  **Fix**: Move `import json` to top-level imports

- **[P3.6]** [cg-architecture] `tests/test_stats.py:14-21` — `_make_arrow_bytes` / `_mock_response` helpers duplicated from `conftest.py`  
  **Why**: If Arrow format changes, the fix must be applied in two places.  
  **Fix**: Remove local helpers from `test_stats.py` and use the `conftest.py` fixtures

- **[P3.7]** [cg-architecture] `pyproject.toml` — `setuptools` as build backend; `hatchling` preferred for `src`-layout  
  **Why**: `hatchling` has simpler configuration with no `setup.cfg` leakage risk for `src`-layout packages.  
  **Fix**: Switch `[build-system]` to `requires = ["hatchling"]` / `build-backend = "hatchling.build"`

- **[P3.8]** [cg-data-quality] `src/povineq/_request.py:40` — Silent `pass` in `_extract_retry_after` discards parse failures  
  **Why**: If the 429 response body is malformed, the function returns `0.0` with no log entry; caller waits 1 second with no visibility.  
  **Fix**: Add `logger.debug("Could not parse retry-after header: ...")` before `pass`

- **[P3.9]** [cg-data-quality] `src/povineq/country_profiles.py:~155` — `unnest_ki()` silently returns empty DataFrame for empty input  
  **Why**: Caller has no indication whether empty output is from genuinely no data or from bad input.  
  **Fix**: Add guard: `if not raw: logger.warning("unnest_ki: received empty response"); return pd.DataFrame()`

- **[P3.10]** [cg-documentation] `src/povineq/_constants.py` — `COLUMN_RENAMES` lacks explanation  
  **Why**: The comment references `pipapi#207` but doesn't explain why renames are needed or when applied.  
  **Fix**: Expand comment: "Renames reconcile PIP API output column names with pipr R package conventions; applied by `parse_response()`"

- **[P3.11]** [cg-testing] `tests/test_utils.py` — Decile array length mismatch and `rename_cols()` duplicate targets untested  
  **Why**: Undefined behavior for varying decile lengths and duplicate rename targets could silently corrupt output.  
  **Fix**: Add parametrized tests for varying decile lengths and duplicate `newnames`

- **[P3.12]** [cg-documentation] `src/povineq/_request.py:121+` — `build_and_execute()` docstring incomplete (cuts off mid-sentence)  
  **Why**: Incomplete API docs leave callers guessing about retry behavior and exception conditions.  
  **Fix**: Complete the docstring with full description of all parameters, retry logic, and raised exceptions

---

### ✅ Passed

- **[cg-version-control]**: No hardcoded secrets or credentials found in `_constants.py`, `_client.py`
- **[cg-version-control]**: `compound-gpid.local.md` correctly gitignored
- **[cg-version-control]**: Strong Python `.gitignore` patterns (`__pycache__/`, `*.pyc`, `.venv/`, etc.)
- **[cg-learnings-researcher]**: Architecture decisions from brainstorm correctly applied — httpx, pydantic, hishel, loguru, Arrow/JSON/CSV dispatch, custom exception hierarchy
- **[cg-learnings-researcher]**: Pydantic validation model pattern (`to_query_params()`) applied correctly for all endpoints except `get_wb()`
- **[cg-learnings-researcher]**: Rate-limit retry logic with exponential backoff correctly implemented
- **[cg-testing]**: `tests/test_validation.py` comprehensively covers `StatsParams` validator logic
- **[cg-testing]**: `tests/test_errors.py` covers all custom exception types
- **[cg-testing]**: `tests/test_constants.py` verifies constant values haven't drifted
