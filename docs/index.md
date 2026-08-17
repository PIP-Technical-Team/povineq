# povineq

**povineq** is a Python wrapper for the [World Bank Poverty and Inequality
Platform (PIP) API](https://pip.worldbank.org/). It gives you access to
household survey-based poverty and inequality estimates for more than 160
countries, covering every year with available data.

If you already use R, `povineq` mirrors the API of the
[`pipr`](https://github.com/worldbank/pipr) package — the same function names,
the same parameter conventions, the same return shapes.

---

## Features

- **Poverty statistics** — headcount ratios, poverty gaps, Gini coefficients,
  mean welfare, and more via `get_stats()`, `get_wb()`, and `get_agg()`.
- **Country profiles** — comprehensive per-country datasets and key indicator
  summaries via `get_cp()` and `get_cp_ki()`.
- **Auxiliary data** — GDP, CPI, PPP, population, survey metadata, and coverage
  tables via `get_aux()` and its per-table convenience wrappers.
- **Connection pooling and retries** — HTTP requests reuse connections and retry
  transient transport failures. Cache-directory helpers are available separately.
- **pandas *or* polars** — every function that returns a DataFrame accepts a
  `dataframe_type` argument so you can work with either library.
- **Typed errors** — `PIPError`, `PIPAPIError`, `PIPRateLimitError`, and
  `PIPConnectionError` make error handling straightforward.

---

## Installation

!!! note "Published releases"
    Install the package from PyPI when using a published release:

    ```bash
    pip install povineq
    ```

For optional [polars](https://pola.rs/) support:

```bash
pip install "povineq[polars]"
```

The package supports Python 3.10 through 3.13. For unreleased development
versions, install from GitHub:

```bash
pip install git+https://github.com/PIP-Technical-Team/povineq.git
pip install "povineq[polars] @ git+https://github.com/PIP-Technical-Team/povineq.git"
```

Releases are intended to be validated and published by
`.github/workflows/publish.yml` using PyPI trusted publishing. Before the first
release, configure the protected `pypi` environment and register owner
`PIP-Technical-Team`, repository `povineq`, workflow `publish.yml`, and
environment `pypi` as the trusted publisher. No credentials belong in the
documentation or repository.

---

## Quick Start

```python
import povineq

# Poverty statistics for a single country and year
df = povineq.get_stats(country="AGO", year=2000)

# All countries, gap-filled estimates
df = povineq.get_stats(fill_gaps=True)

# World Bank regional/global aggregates
df = povineq.get_wb()

# Country profiles
df = povineq.get_cp(country="IDN")
df = povineq.get_cp_ki(country="IDN")

# Auxiliary data
tables = povineq.get_aux()        # list available tables
gdp    = povineq.get_aux("gdp")  # fetch a specific table
cpi    = povineq.get_cpi()       # convenience wrapper

# API info and cache management
print(povineq.check_api())
print(povineq.get_versions())
povineq.delete_cache()
```

---

## Next Steps

- [Getting Started](getting-started.md) — step-by-step installation and your
  first query.
- [Tutorials](tutorials/poverty-statistics.md) — in-depth walkthroughs for each
  function family.
- [API Reference](reference/index.md) — full parameter documentation for every exported
  symbol.

---

## Data Source

All data come from the World Bank
[Poverty and Inequality Platform (PIP)](https://pip.worldbank.org/). See the
[PIP methodology note](https://datanalytics.worldbank.org/pip-methodology/) for
details on how estimates are produced.
