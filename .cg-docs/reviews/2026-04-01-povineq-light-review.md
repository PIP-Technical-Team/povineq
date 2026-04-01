# Review Report

**Review depth**: light
**Date**: 2026-04-01
**Files reviewed**: 34 (14 source + 14 test + pyproject.toml + CI + config)
**Findings**: 4 P1 · 18 P2 · 10 P3

---

## P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality] `src/povineq/__init__.py:67` — Bare `except Exception:` is too broad
  **Why**: Catches the intended `ImportError` but silently masks any other unexpected exception.
  **Fix**: Change to `except (ImportError, AttributeError):`.

- **[P1.2]** [cg-testing] `tests/test_client.py` — `get_client()` function is entirely untested
  **Why**: Core infrastructure (HTTP client, caching, retries, headers, timeout) is only mocked in other tests but never validated directly.
  **Fix**: Add tests verifying `get_client()` returns an `httpx.Client`, sets the correct User-Agent, timeout, base URL, and configures hishel caching.

- **[P1.3]** [cg-testing] `tests/test_request.py:123` — Retry logic for 429 responses is not tested
  **Why**: `build_and_execute()` retry mechanism is critical for reliability; tests mock the function itself rather than testing its behavior.
  **Fix**: Add tests for actual retry behavior: multiple 429s before success, `_MAX_RETRY_SECONDS` cap, retry-count limit, wait-time application.

- **[P1.4]** [cg-testing] `tests/test_response.py:148` — Missing test for `parse_response()` with missing `Content-Type` header
  **Why**: `resp.headers = {}` could cause an unhandled `KeyError`.
  **Fix**: Add `test_missing_content_type_header_raises()` expecting `PIPError`.

---

## P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `src/povineq/stats.py:5,15-16` — Unused import `TYPE_CHECKING` and dead `if TYPE_CHECKING: pass` block
  **Fix**: Remove `TYPE_CHECKING` from import; delete the empty block.

- **[P2.2]** [cg-code-quality] `src/povineq/_response.py:8,19-20` — Same unused `TYPE_CHECKING` and dead block
  **Fix**: Same as P2.1.

- **[P2.3]** [cg-code-quality] `src/povineq/_cache.py:50` — f-string in loguru logger call
  **Why**: f-strings are evaluated even when the log level suppresses the message.
  **Fix**: `logger.info("All {} cached item(s) have been deleted.", len(cached))`.

- **[P2.4]** [cg-code-quality] `src/povineq/_request.py:127` — f-string in loguru logger call
  **Fix**: `logger.debug("GET request", url=url, params=params)`.

- **[P2.5]** [cg-code-quality] `src/povineq/_request.py:141` — f-string in loguru logger call
  **Fix**: `logger.warning("Rate limit hit", wait_seconds=wait, attempt=attempt + 1)`.

- **[P2.6]** [cg-code-quality] `src/povineq/auxiliary.py:90` — f-string in loguru logger call
  **Fix**: `logger.info("Available auxiliary tables", tables=tables_list)`.

- **[P2.7]** [cg-code-quality] `src/povineq/auxiliary.py:166` — f-string in loguru logger call inside loop
  **Fix**: Log the whole list once outside the loop, or use structured logging.

- **[P2.8]** [cg-code-quality] `src/povineq/country_profiles.py:60` — f-string in loguru logger call
  **Fix**: `logger.debug("get_cp", country=country, povline=povline, ppp_version=ppp_version)`.

- **[P2.9]** [cg-code-quality] `src/povineq/country_profiles.py:122` — f-string in loguru logger call
  **Fix**: `logger.debug("get_cp_ki", country=country, povline=povline)`.

- **[P2.10]** [cg-code-quality] `src/povineq/stats.py:87-89` — Multi-line f-string in loguru logger call
  **Fix**: `logger.debug("get_stats", country=country, year=year, povline=povline, popshare=popshare, fill_gaps=fill_gaps, nowcast=nowcast, subgroup=subgroup)`.

- **[P2.11]** [cg-code-quality] `src/povineq/country_profiles.py:207` — `DataFrame.drop_duplicates(inplace=True)` inside loop
  **Why**: `inplace=True` is discouraged; mutates while the reference is still in scope.
  **Fix**: `df_ref = df_ref.drop_duplicates(subset=merge_cols)`.

- **[P2.12]** [cg-testing] `tests/test_response.py:175` — Missing test for Arrow-to-Polars zero-copy conversion
  **Fix**: Add `test_arrow_table_to_polars_zero_copy()`.

- **[P2.13]** [cg-testing] `tests/test_request.py` — Missing test for `_parse_api_error()` when `details` is a list
  **Fix**: Add a test with `"details": [{"field": "x", "msg": "y"}]`.

- **[P2.14]** [cg-testing] `tests/test_stats.py` — Missing edge-case parameter interaction tests
  **Fix**: Add parametrized tests for `subgroup` + `povline` + `popshare`; `fill_gaps=False` with `subgroup`; multiple countries + years as lists.

- **[P2.15]** [cg-testing] `tests/test_auxiliary.py:70` — Missing test for `get_aux(assign_tb=True, simplify=False)`
  **Fix**: Add `test_assign_tb_with_simplify_false_logs_warning()`.

- **[P2.16]** [cg-testing] `tests/test_utils.py:34` — Missing test for `change_grouped_stats_to_csv()` with empty deciles list
  **Fix**: Add `test_empty_decile_list_handled()`.

- **[P2.17]** [cg-testing] `tests/test_utils.py:33` — Missing test for `rename_cols()` with empty lists
  **Fix**: Add `test_empty_rename_lists()` asserting the DataFrame is returned unchanged.

- **[P2.18]** [cg-testing] `tests/test_country_profiles.py` — Missing test for `get_cp()` with list of countries
  **Fix**: Add `test_get_cp_with_country_list()` verifying `params["country"] == "AGO,ALB"`.

- **[P2.19]** [cg-testing] `tests/test_country_profiles.py:144` — `unnest_ki()` tested only for the basic nesting pattern
  **Fix**: Add tests for wrapped list-of-lists, mixed nulls, and missing keys.

- **[P2.20]** [cg-testing] `tests/conftest.py:88,96` — Unused fixtures `error_404_bytes` and `rate_limit_bytes`
  **Fix**: Either add tests that use them or remove them.

---

## P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `src/povineq/utils.py:44` — `Series.apply(lambda v: isinstance(...))` — not vectorised
  **Fix**: Use `.map(lambda v: isinstance(v, (list, tuple)))` or document as intentional.

- **[P3.2]** [cg-code-quality] `src/povineq/utils.py:45` — `Series.apply(len)` — not vectorised
  **Fix**: Use `.map(len)`.

- **[P3.3]** [cg-code-quality] `src/povineq/utils.py:62-64` — Multiple chained `.apply(lambda)` for decile extraction
  **Fix**: Consider `pd.DataFrame(deciles_series.tolist())` or document the irregular structure.

- **[P3.4]** [cg-code-quality] `src/povineq/_cache.py:47` — Redundant `hasattr(_cache_dir, "cache_clear")` check
  **Fix**: `@functools.lru_cache` always provides `cache_clear`; call it directly.

- **[P3.5]** [cg-testing] `tests/test_response.py:95-141` — Copy-paste across Arrow/JSON/CSV test classes
  **Fix**: Collapse into `@pytest.mark.parametrize` over format fixtures.

- **[P3.6]** [cg-testing] `tests/test_client.py:22-35` — Duplicate pattern for server env-var tests
  **Fix**: Parametrize over `(server, env_var, url)`.

- **[P3.7]** [cg-testing] `tests/test_stats.py:47-93` — Repetitive endpoint-routing tests
  **Fix**: Parametrize or extract a shared helper.

- **[P3.8]** [cg-testing] `tests/test_response.py:192-205` — `_to_target_type()` missing pandas-to-polars and arrow-to-polars cases
  **Fix**: Add parametrized tests for all 4 `(input_type, output_format)` combinations.

- **[P3.9]** [cg-testing] `tests/test_response.py:180` — Fragile `sys.modules` monkeypatching for polars-absent test
  **Fix**: Assert the error message matches `"polars is not installed"`.

- **[P3.10]** [cg-testing] `tests/test_validation.py:199` — Missing test for `CpKiParams(country="")` rejection
  **Fix**: Add `test_country_empty_string_invalid()` expecting `ValidationError`.

---

## Passed

- cg-code-quality: General structure, modularity, docstrings, error hierarchy, type hints — no issues.
- cg-testing: Test infrastructure (conftest, fixtures, respx mocking) — solid foundation.
