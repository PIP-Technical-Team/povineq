---
date: 2026-03-31
title: "povineq v1.0 — Full implementation plan"
status: active
brainstorm: ".cg-docs/brainstorms/2026-03-31-povineq-architecture-and-stack.md"
language: "Python"
estimated-effort: "large"
tags: [python, package, api-client, pip-api, v1.0, full-implementation]
---

# Plan: povineq v1.0 — Full Implementation

## Objective

Build a complete Python package (`povineq`) that wraps the World Bank PIP API with
full feature parity to the `pipr` R package (excluding `get_gd()`, deferred to v2.0).
The package uses `httpx` + `pydantic` + `hishel` + `pyarrow`, returns pandas DataFrames
by default (polars optional), is published to PyPI, and is thoroughly tested.

## Context

- The `pipr` R package (v1.4.0.9000) has 17+ exported functions across 5 categories.
- Architecture brainstorm chose: httpx, pydantic v2, hishel, pyarrow, loguru, pytest.
- Production API base URL: `https://api.worldbank.org/pip`
- API version: `v1` (only version currently)
- Endpoints: `pip`, `pip-grp`, `aux`, `cp-download`, `cp-key-indicators`, `health-check`,
  `versions`, `pip-info`
- Response formats: Arrow (preferred), JSON, CSV (no RDS in Python)
- The project root is currently empty (only README.md, LICENSE, .gitignore, config files).

## Implementation Steps

### 1. Package Scaffolding

**Files to create**:
```
src/povineq/
├── __init__.py          # Public API exports
├── _constants.py        # Base URL, user agent, endpoints, defaults
├── _client.py           # HTTP client setup (httpx + hishel + retry)
├── _request.py          # Request builder (URL + params + caching)
├── _response.py         # Response parser (Arrow/JSON/CSV dispatch)
├── _errors.py           # Custom exceptions (PIPError, RateLimitError, etc.)
├── _validation.py       # Pydantic models for parameter validation
├── _cache.py            # Cache management (delete, info)
├── _aux_store.py        # In-memory auxiliary table store (like .pip env)
├── stats.py             # get_stats(), get_wb(), get_agg()
├── country_profiles.py  # get_cp(), get_cp_ki(), unnest_ki()
├── aux.py               # get_aux(), display_aux(), call_aux(), all get_* wrappers
├── info.py              # check_api(), get_versions(), get_pip_info()
├── utils.py             # change_grouped_stats_to_csv(), rename helpers
├── py.typed             # PEP 561 marker for type checkers
tests/
├── conftest.py          # Shared fixtures, skip markers
├── fixtures/            # Saved API responses for offline tests
│   ├── res_arrow.feather
│   ├── res_json.json
│   ├── res_csv.csv
│   └── res_error_404.json
├── test_client.py       # HTTP client and request building
├── test_response.py     # Response parsing for all formats
├── test_stats.py        # get_stats, get_wb, get_agg
├── test_country_profiles.py  # get_cp, get_cp_ki
├── test_aux.py          # get_aux and all wrappers
├── test_info.py         # check_api, get_versions, get_pip_info
├── test_cache.py        # Cache delete/info
├── test_validation.py   # Parameter validation edge cases
├── test_utils.py        # Utility function tests
pyproject.toml           # Project metadata, deps, build config
```

**Details**:
- Use `src/` layout per project conventions.
- `pyproject.toml` with `hatch` build backend or `setuptools` with `build`.
- Define `[project]` metadata: name="povineq", version="0.1.0", requires-python=">=3.10".
- Dependencies: `httpx>=0.27`, `hishel>=0.1`, `pydantic>=2.0`, `pyarrow>=15.0`,
  `pandas>=2.0`, `loguru>=0.7`.
- Optional dependencies: `polars>=1.0` (under `[project.optional-dependencies] polars`).
- Dev dependencies: `pytest>=8.0`, `pytest-httpx>=0.30`, `ruff>=0.5`, `mypy>=1.10`.

**Tests**: Verify package imports correctly, `__version__` accessible.

**Acceptance criteria**: `pip install -e .` succeeds; `import povineq` works; `pytest` discovers test files.

---

### 2. Constants and Configuration

**Files**: `src/povineq/_constants.py`

**Details**:
```python
PROD_URL = "https://api.worldbank.org/pip"
USER_AGENT = "povineq (https://github.com/PIP-Technical-Team/povineq)"
API_VERSION = "v1"

# Endpoints
ENDPOINT_PIP = "pip"
ENDPOINT_PIP_GRP = "pip-grp"
ENDPOINT_AUX = "aux"
ENDPOINT_CP_DOWNLOAD = "cp-download"
ENDPOINT_CP_KEY_INDICATORS = "cp-key-indicators"
ENDPOINT_HEALTH_CHECK = "health-check"
ENDPOINT_VERSIONS = "versions"
ENDPOINT_PIP_INFO = "pip-info"

# Server environment variable names
ENV_QA_URL = "PIP_QA_URL"
ENV_DEV_URL = "PIP_DEV_URL"

# Default parameter values
DEFAULT_COUNTRY = "all"
DEFAULT_YEAR = "all"
DEFAULT_POVLINE_CP = 2.15
DEFAULT_POVLINE_CP_2011 = 1.9
DEFAULT_PPP_VERSION = 2017
DEFAULT_FORMAT = "arrow"
DEFAULT_FORMAT_AUX = "json"  # aux doesn't support arrow

# Column rename mapping (temporary fix matching pipr)
COLUMN_RENAMES = {
    "survey_year": "welfare_time",
    "reporting_year": "year",
    "reporting_pop": "pop",
    "reporting_gdp": "gdp",
    "reporting_pce": "hfce",
    "pce_data_level": "hfce_data_level",
}
```

**Tests**: Verify constant values match expected API contract.

**Acceptance criteria**: All constants importable; match `pipr`'s values.

---

### 3. Custom Exceptions

**Files**: `src/povineq/_errors.py`

**Details**:
```python
class PIPError(Exception):
    """Base exception for PIP API errors."""

class PIPAPIError(PIPError):
    """API returned an error response (4xx/5xx)."""
    # Stores: status_code, error_message, details, valid_values

class PIPRateLimitError(PIPError):
    """API rate limit exceeded (429)."""
    # Stores: retry_after_seconds

class PIPConnectionError(PIPError):
    """Network connectivity issue."""

class PIPValidationError(PIPError):
    """Invalid parameter values (caught before API call)."""
```

Map to `pipr` patterns:
- `parse_error_body()` → `PIPAPIError` with structured fields
- `pip_is_transient()` → `PIPRateLimitError`
- `check_internet()` → `PIPConnectionError`
- pydantic validation → `PIPValidationError`

**Tests**: Verify exception hierarchy; verify string representations.

**Acceptance criteria**: All exceptions importable; correct inheritance chain.

---

### 4. Parameter Validation (Pydantic Models)

**Files**: `src/povineq/_validation.py`

**Details** — Define pydantic models for each endpoint's parameters:

```python
class StatsParams(BaseModel):
    country: str | list[str] = "all"
    year: str | int | list[int] = "all"
    povline: float | None = None
    popshare: float | None = None
    fill_gaps: bool = False
    nowcast: bool = False
    subgroup: str | None = None  # None, "wb_regions", "none"
    welfare_type: Literal["all", "income", "consumption"] = "all"
    reporting_level: Literal["all", "national", "urban", "rural"] = "all"
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["arrow", "json", "csv"] = "arrow"

    # Validators:
    # - If popshare is set, nullify povline
    # - If nowcast=True, force fill_gaps=True
    # - If fill_gaps=False, force nowcast=False
    # - If subgroup is set, clear fill_gaps/nowcast

class CpParams(BaseModel):
    country: str | list[str] = "all"
    povline: float | None = 2.15
    version: str | None = None
    ppp_version: int = 2017
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["arrow", "json", "csv"] = "arrow"

    # Validator: if ppp_version == 2011 and povline is None → set 1.9

class CpKiParams(BaseModel):
    country: str  # REQUIRED, single value only
    povline: float | None = 2.15
    version: str | None = None
    ppp_version: int = 2017
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"

    # Validator: country must be single string (not list, not None)

class AuxParams(BaseModel):
    table: str | None = None
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["json", "csv"] = "json"  # aux doesn't support arrow/rds

class AggParams(BaseModel):
    year: str | int | list[int] = "all"
    povline: float | None = None
    version: str | None = None
    ppp_version: int | None = None
    release_version: str | None = None
    aggregate: str | None = None
    api_version: Literal["v1"] = "v1"
    format: Literal["json", "csv"] = "json"
```

Each model includes a `to_query_params()` method that:
- Converts list params to comma-separated strings
- Removes None values
- Converts booleans to lowercase strings

**Tests**: Test each model with valid/invalid inputs; test validators fire correctly;
test `to_query_params()` output.

**Acceptance criteria**: All pydantic models validate correctly; match `pipr` parameter
behavior (popshare nullifies povline, nowcast implies fill_gaps, etc.).

---

### 5. HTTP Client and Request Builder

**Files**: `src/povineq/_client.py`, `src/povineq/_request.py`

**Details**:

`_client.py` — Singleton-style client management:
```python
def get_client(server: str | None = None) -> httpx.Client:
    """Get configured httpx client with caching and retry."""
    base_url = select_base_url(server)
    storage = hishel.FileStorage(base_path=_cache_dir())
    controller = hishel.Controller(allow_stale=True)
    transport = hishel.CacheTransport(
        transport=httpx.HTTPTransport(retries=3),
        storage=storage,
        controller=controller,
    )
    return httpx.Client(
        base_url=base_url,
        transport=transport,
        headers={"User-Agent": USER_AGENT},
        timeout=60.0,
    )

def select_base_url(server: str | None) -> str:
    """Select API base URL based on server parameter."""
    # "prod"/None → PROD_URL
    # "qa" → os.environ["PIP_QA_URL"]
    # "dev" → os.environ["PIP_DEV_URL"]
```

`_request.py` — Request construction and execution:
```python
def build_and_execute(
    endpoint: str,
    params: dict[str, str],
    server: str | None = None,
    api_version: str = "v1",
) -> httpx.Response:
    """Build URL, execute GET, handle rate-limit retry."""
    client = get_client(server)
    url = f"/{api_version}/{endpoint}"
    response = client.get(url, params=params)

    # Rate limit handling (429)
    if response.status_code == 429:
        retry_seconds = _extract_retry_after(response)
        raise PIPRateLimitError(retry_seconds)

    # Error handling (4xx/5xx)
    if response.is_error:
        raise _parse_error(response)

    return response
```

Rate limit retry logic:
- Detect 429 with "Rate limit is exceeded" in body
- Extract wait time from message: `"Try again in {N} seconds"`
- Implement retry with exponential backoff up to 60s max

**Tests**: Mock HTTP responses; test URL construction; test rate-limit retry; test
server selection (prod/qa/dev); test error parsing.

**Acceptance criteria**: Can build and execute requests to all endpoints; rate-limit
retry works; errors are parsed into structured exceptions.

---

### 6. Response Parser

**Files**: `src/povineq/_response.py`

**Details**:
```python
def parse_response(
    response: httpx.Response,
    simplify: bool = True,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | pl.DataFrame | PIPResponse:
    """Parse API response based on Content-Type header."""
    content_type = response.headers.get("content-type", "")

    if "application/vnd.apache.arrow.file" in content_type:
        df = _parse_arrow(response.content)
    elif "application/json" in content_type:
        df = _parse_json(response.text)
    elif "text/csv" in content_type:
        df = _parse_csv(response.text)
    else:
        raise PIPError(f"Unsupported content type: {content_type}")

    # Post-processing: pivot grouped stats deciles
    df = change_grouped_stats_to_csv(df)

    # Column renaming (temporary API compatibility fix)
    df = _rename_columns(df)

    if simplify:
        return _to_dataframe(df, dataframe_type)
    else:
        return PIPResponse(
            url=str(response.url),
            status=response.status_code,
            content_type=content_type,
            content=_to_dataframe(df, dataframe_type),
            response=response,
        )
```

Format-specific parsers:
- Arrow: `pyarrow.ipc.read_feather(io.BytesIO(content))` → pandas/polars
- JSON: `json.loads(text)` → pandas `pd.json_normalize()` or `pd.DataFrame()`
- CSV: `pd.read_csv(io.StringIO(text))` or `pl.read_csv(io.StringIO(text))`

`PIPResponse` dataclass (equivalent to `pipr`'s `pip_api` S3 class):
```python
@dataclass
class PIPResponse:
    url: str
    status: int
    content_type: str
    content: pd.DataFrame | pl.DataFrame
    response: httpx.Response
```

**Tests**: Test each format parser with saved fixture files; test simplify=True/False;
test column renaming; test decile pivoting; test pandas vs polars output.

**Acceptance criteria**: All 3 response formats parse correctly; simplify toggle works;
column renaming matches `pipr`; grouped stats decile pivoting matches `pipr`.

---

### 7. Cache Management

**Files**: `src/povineq/_cache.py`

**Details**:
```python
def _cache_dir() -> Path:
    """Return platform-appropriate cache directory."""
    # Use platformdirs.user_cache_dir("povineq")

def delete_cache() -> None:
    """Delete all cached HTTP responses."""

def get_cache_info() -> dict:
    """Return cache statistics (file count, total size, path)."""
```

**Tests**: Create temp cache; verify delete clears it; verify info reports correctly.

**Acceptance criteria**: Cache dir is platform-appropriate; delete/info work correctly.

---

### 8. Auxiliary Table Store

**Files**: `src/povineq/_aux_store.py`

**Details** — In-memory store equivalent to `pipr`'s `.pip` environment:
```python
_store: dict[str, pd.DataFrame] = {}

def set_aux(table: str, value: pd.DataFrame, replace: bool = False) -> None:
    """Store auxiliary table in memory."""

def call_aux(table: str | None = None) -> pd.DataFrame | list[str]:
    """Retrieve stored table, or list available tables if table=None."""
```

**Tests**: Store/retrieve tables; test replace logic; test listing.

**Acceptance criteria**: Tables persist in-memory across function calls; listing works.

---

### 9. Core Stats Functions

**Files**: `src/povineq/stats.py`

**Details**:

```python
def get_stats(
    country: str | list[str] = "all",
    year: str | int | list[int] = "all",
    povline: float | None = None,
    popshare: float | None = None,
    fill_gaps: bool = False,
    nowcast: bool = False,
    subgroup: str | None = None,
    welfare_type: str = "all",
    reporting_level: str = "all",
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = "v1",
    format: str = "arrow",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: str = "pandas",
) -> pd.DataFrame | PIPResponse:
```

Logic flow (mirrors `pipr` exactly):
1. Validate params via `StatsParams` pydantic model
2. Route: if `subgroup` → endpoint=`pip-grp` + set `group_by`; else → `pip`
3. Build query params, execute request
4. Parse response
5. If `nowcast=False` and `simplify=True`: filter out nowcast rows

```python
def get_wb(
    year="all", povline=None, version=None, ppp_version=None,
    release_version=None, api_version="v1", format="json",
    simplify=True, server=None, dataframe_type="pandas",
) -> pd.DataFrame | PIPResponse:
    """World Bank regional aggregates. Shorthand for get_stats(subgroup='wb_regions')."""

def get_agg(
    year="all", povline=None, version=None, ppp_version=None,
    release_version=None, aggregate=None, api_version="v1",
    format="json", simplify=True, server=None, dataframe_type="pandas",
) -> pd.DataFrame | PIPResponse:
    """Custom aggregates (fcv, regional, vintage, etc.)."""
```

**Tests** (mirroring `pipr`'s test-get_stats.R):
- Single country-year query
- Multiple countries/years
- All countries/years (default)
- fill_gaps=True
- popshare parameter
- subgroup routing (wb_regions, none)
- All format types
- simplify=True/False
- nowcast filtering
- get_wb() returns regional aggregates
- get_agg() with different aggregate values
- Invalid parameter errors

**Acceptance criteria**: `get_stats("ALB")` returns same columns and row count as
`pipr::get_stats(country="ALB")`; all edge cases match `pipr` behavior.

---

### 10. Country Profile Functions

**Files**: `src/povineq/country_profiles.py`

**Details**:

```python
def get_cp(
    country="all", povline=2.15, version=None, ppp_version=2017,
    release_version=None, api_version="v1", format="arrow",
    simplify=True, server=None, dataframe_type="pandas",
) -> pd.DataFrame | PIPResponse:
    """Country profiles download."""
    # Conditional default: if ppp_version == 2011 and povline is None → 1.9
    # Endpoint: cp-download

def get_cp_ki(
    country: str,  # REQUIRED, single value
    povline=2.15, version=None, ppp_version=2017,
    release_version=None, api_version="v1",
    simplify=True, server=None, dataframe_type="pandas",
) -> pd.DataFrame | PIPResponse:
    """Country profile key indicators."""
    # Validation: country required, single string only
    # If simplify=True: call unnest_ki() on response
    # Endpoint: cp-key-indicators

def unnest_ki(data: pd.DataFrame) -> pd.DataFrame:
    """Flatten nested key indicators into single DataFrame."""
    # Extract nested dfs: headcount, headcount_national, mpm_headcount,
    #   pop, gni, gdp_growth, shared_prosperity
    # Deduplicate on (country_code, reporting_year)
    # Merge all on (country_code, reporting_year)
```

**Tests** (mirroring test-get_cp.R, test-get_cp_ki.R):
- Default parameters
- Conditional povline logic (2011 PPP → 1.9)
- Country validation in get_cp_ki (required, single value)
- Unnesting produces flat table
- Invalid country errors

**Acceptance criteria**: Output matches `pipr::get_cp()` and `pipr::get_cp_ki()` column
structure and values.

---

### 11. Auxiliary Data Functions

**Files**: `src/povineq/aux.py`

**Details**:

```python
def get_aux(
    table: str | None = None,
    version=None, ppp_version=None, release_version=None,
    api_version="v1", format="json",
    simplify=True, server=None, dataframe_type="pandas",
    assign_tb: bool | str = False, replace: bool = False,
) -> pd.DataFrame | list[str] | PIPResponse:
    """Fetch auxiliary tables."""
    # If table=None: return list of available tables
    # If assign_tb: store in _aux_store
    # Endpoint: aux

def display_aux(**kwargs) -> pd.DataFrame:
    """Display available auxiliary tables."""
    # Fetch table list, print formatted output

def call_aux(table: str | None = None) -> pd.DataFrame | list[str]:
    """Retrieve table from in-memory store."""

# Convenience wrappers — all delegate to get_aux(table=<name>)
def get_countries(**kwargs): return get_aux(table="countries", **kwargs)
def get_regions(**kwargs): return get_aux(table="regions", **kwargs)
def get_cpi(**kwargs): return get_aux(table="cpi", **kwargs)
def get_dictionary(**kwargs): return get_aux(table="dictionary", **kwargs)
def get_gdp(**kwargs): return get_aux(table="gdp", **kwargs)
def get_incgrp_coverage(**kwargs): return get_aux(table="incgrp_coverage", **kwargs)
def get_interpolated_means(**kwargs): return get_aux(table="interpolated_means", **kwargs)
def get_hfce(**kwargs): return get_aux(table="pce", **kwargs)
def get_pop(**kwargs): return get_aux(table="pop", **kwargs)
def get_pop_region(**kwargs): return get_aux(table="pop_region", **kwargs)
def get_ppp(**kwargs): return get_aux(table="ppp", **kwargs)
def get_region_coverage(**kwargs): return get_aux(table="region_coverage", **kwargs)
def get_survey_means(**kwargs): return get_aux(table="survey_means", **kwargs)
```

**Tests** (mirroring test-get_aux.R):
- No table specified → returns list
- Specific table names
- All format types
- Simplify toggle
- assign_tb stores in memory
- call_aux retrieves stored tables
- Each convenience wrapper returns correct table
- Invalid table name error

**Acceptance criteria**: All 13 convenience wrappers return correct data; in-memory
store works identically to `pipr`'s `.pip` environment.

---

### 12. Info/Utility Functions

**Files**: `src/povineq/info.py`, `src/povineq/utils.py`

**Details**:

`info.py`:
```python
def check_api(api_version="v1", server=None) -> dict:
    """Test API connectivity."""
    # Hit health-check endpoint

def get_versions(api_version="v1", server=None, simplify=True, dataframe_type="pandas"):
    """List available data versions."""
    # Hit versions endpoint

def get_pip_info(api_version="v1", server=None) -> dict:
    """Get API metadata."""
    # Hit pip-info endpoint
```

`utils.py`:
```python
def change_grouped_stats_to_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Convert deciles list column into individual decile1..decile10 columns."""
```

**Tests**: Test API health check (mocked); test versions returns dataframe; test
pip_info returns dict; test decile pivoting with sample data.

**Acceptance criteria**: Functions match `pipr` behavior; decile pivoting produces
same column structure.

---

### 13. Public API (`__init__.py`)

**Files**: `src/povineq/__init__.py`

**Details** — Export all public functions:
```python
from povineq.stats import get_stats, get_wb, get_agg
from povineq.country_profiles import get_cp, get_cp_ki
from povineq.aux import (
    get_aux, display_aux, call_aux,
    get_countries, get_regions, get_cpi, get_dictionary,
    get_gdp, get_incgrp_coverage, get_interpolated_means,
    get_hfce, get_pop, get_pop_region, get_ppp,
    get_region_coverage, get_survey_means,
)
from povineq.info import check_api, get_versions, get_pip_info
from povineq._cache import delete_cache, get_cache_info
from povineq.utils import change_grouped_stats_to_csv
from povineq._errors import (
    PIPError, PIPAPIError, PIPRateLimitError,
    PIPConnectionError, PIPValidationError,
)

__version__ = "0.1.0"
```

**Tests**: Verify all public names accessible from `import povineq`.

**Acceptance criteria**: `dir(povineq)` includes all exported functions; no private
names leak.

---

### 14. Test Infrastructure and Fixtures

**Files**: `tests/conftest.py`, `tests/fixtures/`

**Details**:

`conftest.py`:
```python
import pytest

@pytest.fixture
def skip_if_offline():
    """Skip test if no internet connectivity."""

@pytest.fixture
def mock_client(monkeypatch):
    """Mock httpx client for offline testing."""

@pytest.fixture
def sample_arrow_response():
    """Load saved Arrow response from fixtures."""

@pytest.fixture
def sample_json_response():
    """Load saved JSON response from fixtures."""
```

Capture real API responses to save as fixtures:
- One Arrow response from `get_stats()`
- One JSON response from `get_aux()`
- One CSV response
- One error response (404)
- One rate-limit response (429)

Marker system:
- `@pytest.mark.online` — requires internet (skipped in CI by default)
- `@pytest.mark.slow` — long-running tests

**Acceptance criteria**: Tests can run fully offline using fixtures; online tests
skipped gracefully without internet.

---

### 15. Documentation and README

**Files**: `README.md` (update), `docs/` (optional), docstrings in all modules

**Details**:
- Update README.md with: installation, quick start, full API reference, examples
- Every public function has Google-style docstrings with Args, Returns, Raises, Example
- Module-level docstrings in every .py file

README structure:
```markdown
# povineq
Python wrapper for the World Bank PIP API.

## Installation
pip install povineq

## Quick Start
import povineq
df = povineq.get_stats(country="ALB")

## API Reference
### Core Statistics
### Country Profiles
### Auxiliary Data
### Utilities

## Configuration
### Server Selection
### Caching
### DataFrame Type (pandas vs polars)

## Contributing
## License
```

**Acceptance criteria**: README has working examples; all public functions documented.

---

### 16. CI/CD and PyPI Publishing

**Files**: `.github/workflows/test.yml`, `.github/workflows/publish.yml`

**Details**:
- GitHub Actions workflow: lint (ruff), type check (mypy), test (pytest) on Python 3.10-3.13
- Publish to PyPI on tagged releases via trusted publishing
- Codecov integration

**Acceptance criteria**: CI passes on all supported Python versions; package publishable.

---

## Testing Strategy

### Test Categories

| Category | Count (est.) | Approach |
|----------|-------------|----------|
| Unit tests (validation, parsing, utils) | ~40 | Fully offline, fixture-based |
| Integration tests (API functions) | ~30 | Mocked HTTP, fixture responses |
| Online tests (real API) | ~20 | Marked `@pytest.mark.online`, skipped in CI |
| Edge cases (rate limits, errors, empty responses) | ~15 | Mocked |

### Key Test Scenarios (from pipr)
- Single/multiple country and year queries
- All default parameters
- fill_gaps, nowcast, popshare toggling
- Subgroup routing (pip vs pip-grp)
- Format switching (arrow, json, csv)
- Simplify toggle (DataFrame vs PIPResponse)
- Conditional defaults (povline/ppp_version logic)
- Rate limit retry behavior
- Error response parsing (404, 429, 502, 504)
- Column renaming
- Decile pivoting
- Auxiliary table store lifecycle
- Cache create/info/delete

### Coverage Target
- Minimum 85% line coverage
- 100% coverage on validation and error handling modules

## Documentation Checklist

- [ ] Google-style docstrings on all public functions
- [ ] Module-level docstrings on all .py files
- [ ] README with installation, quick start, examples
- [ ] API reference section in README or dedicated docs
- [ ] CONTRIBUTING.md
- [ ] Type hints on all functions (PEP 561 `py.typed` marker)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PIP API changes response format | Parsing breaks | Pin API version (v1); response format auto-detection |
| hishel lacks needed caching features | Caching incomplete | Fall back to manual disk caching with `diskcache` |
| Arrow format not returned for all endpoints | Some endpoints fail | Always have JSON/CSV fallback; aux endpoints use JSON default |
| Rate limiting during heavy testing | Tests fail | Use fixtures for offline tests; online tests are opt-in |
| Polars optional dependency causes import errors | User confusion | Lazy import; clear error message if polars not installed |

## Out of Scope (v1.0)

- `get_gd()` — grouped data (deferred to v2.0)
- CLI interface (deferred to v2.0)
- Async API (deferred to v2.0, but httpx is async-ready)
- In-memory memoization (start with disk cache only)
- Jupyter/notebook display integration
