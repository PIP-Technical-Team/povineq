---
date: 2026-03-31
title: "povineq Python package — architecture and stack decisions"
status: decided
chosen-approach: "httpx + pydantic + hishel (Modern Stack)"
tags: [architecture, python, api-client, pip-api, package-design]
---

# povineq Python Package — Architecture and Stack Decisions

## Context

The team needs to build `povineq`, a Python wrapper for the PIP API that replicates the functionality of the `pipr` R package. The package must be efficient, robust, well-tested, and published to PyPI for external users.

## Requirements

- **Full parity with `pipr`** (all exported functions except `get_gd()`, which is deferred to v2.0)
- **Target audience**: External researchers and general public, plus World Bank staff
- **Distribution**: Published to PyPI (`pip install povineq`)
- **Data output**: pandas DataFrame by default, polars DataFrame as option
- **Wire format**: Arrow (preferred) from API, with JSON/CSV fallback
- **Caching**: Disk-based HTTP caching (like `httr2::req_cache()`)
- **No CLI needed for v1.0** (can be added later as thin wrapper)
- **API handles multi-country/multi-poverty-line in single requests** — no need for client-side request batching

### Functions to implement (v1.0)

**Core stats:**
- `get_stats(country, year, povline, popshare, fill_gaps, nowcast, subgroup, welfare_type, reporting_level, version, ppp_version, release_version, api_version, format, simplify, server)`
- `get_wb(year, povline, version, ppp_version, release_version, api_version, format, simplify, server)`
- `get_agg(year, povline, version, ppp_version, release_version, aggregate, api_version, format, simplify, server)`

**Country profiles:**
- `get_cp(country, povline, version, ppp_version, release_version, api_version, format, simplify, server)`
- `get_cp_ki(country, povline, version, ppp_version, release_version, api_version, simplify, server)`

**Auxiliary data:**
- `get_aux(table, ...)` + all convenience wrappers (`get_countries`, `get_regions`, `get_cpi`, `get_dictionary`, `get_gdp`, `get_incgrp_coverage`, `get_interpolated_means`, `get_hfce`, `get_pop`, `get_pop_region`, `get_ppp`, `get_region_coverage`, `get_survey_means`)
- `display_aux()`
- `call_aux(table)`

**Utilities:**
- `check_api()`
- `get_versions()`
- `get_pip_info()`
- `delete_cache()`
- `get_cache_info()`
- `change_grouped_stats_to_csv()`

**Deferred to v2.0:**
- `get_gd()` (grouped data from user-supplied distributions)

## Approaches Considered

### Approach 1: httpx + pydantic + hishel (Modern Stack)

Build on `httpx` for HTTP, `pydantic` for parameter validation and response models, `hishel` for HTTP caching, and `pyarrow` for Arrow format parsing.

**Pros:**
- `httpx` is the current best-practice HTTP library (successor to `requests`)
- `pydantic` gives automatic parameter validation with clear error messages
- `hishel` mirrors `httr2::req_cache()` behavior closely
- Async-ready from day one
- Clean separation: validation → request building → execution → parsing

**Cons:**
- More dependencies than a minimal approach
- `hishel` less well-known than `requests-cache`

**Effort:** Medium

### Approach 2: requests + requests-cache (Conservative Stack)

Use `requests` for HTTP, `requests-cache` for transparent caching, manual validation.

**Pros:**
- `requests` universally known
- `requests-cache` mature

**Cons:**
- Synchronous-only, no async path
- No structured validation
- `requests` in maintenance mode

**Effort:** Medium

### Approach 3: httpx + attrs Minimal (Lightweight Modern)

Use `httpx` with `attrs` and custom caching transport.

**Pros:**
- Fewer dependencies, `attrs` faster at runtime

**Cons:**
- Must build custom caching logic
- Less expressive validation
- More custom code to maintain

**Effort:** Medium-Large

## Decision

**Approach 1: httpx + pydantic + hishel** was chosen for the best balance of modern tooling, maintainability, and feature parity with `pipr`'s `httr2` architecture.

### Technology Stack

| Concern | Library | Rationale |
|---------|---------|-----------|
| HTTP client | `httpx` | Modern, async-capable, successor to `requests` |
| Parameter validation | `pydantic` v2 | Structured validation, clear error messages |
| HTTP caching | `hishel` | RFC 9111 compliant, built on `httpx` |
| Arrow parsing | `pyarrow` | Direct equivalent of R's `arrow::read_feather()` |
| JSON parsing | built-in `json` | Standard library |
| CSV parsing | `pandas` / `polars` | Same libraries used for output |
| Default output | `pandas.DataFrame` | Most widely known |
| Optional output | `polars.DataFrame` | For users who prefer polars |
| Build system | `hatch` or `setuptools` | Standard Python packaging |
| Environment | `uv` | Fast dependency management |
| Testing | `pytest` | Standard |
| Logging | `loguru` | Per project conventions |

## Next Steps

1. Scaffold the Python package structure (`src/povineq/`)
2. Implement core infrastructure: base URL selection, request building, response parsing, caching, retry/rate-limit logic
3. Implement `get_stats()` as the first and most complex function
4. Implement remaining functions following the same pattern
5. Add comprehensive tests mirroring `pipr`'s test suite
6. Set up CI/CD and PyPI publishing
7. Write documentation and README with examples
