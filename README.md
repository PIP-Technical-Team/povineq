# povineq

Python wrapper for the [World Bank PIP API](https://pip.worldbank.org/).
Mirrors the functionality of the [`pipr`](https://github.com/worldbank/pipr) R package.

## Installation

Once the first release is published, install the package from PyPI:

```bash
pip install povineq
# with optional polars support
pip install "povineq[polars]"
```

The package supports Python 3.10 through 3.13. For unreleased development
versions, install directly from GitHub:

```bash
pip install git+https://github.com/PIP-Technical-Team/povineq.git
pip install "povineq[polars] @ git+https://github.com/PIP-Technical-Team/povineq.git"
```

## Quick Start

```python
import povineq

# Poverty statistics for a single country
df = povineq.get_stats(country="AGO", year=2000)

# All countries, gap-filled
df = povineq.get_stats(fill_gaps=True)

# World Bank regional aggregates
df = povineq.get_wb()

# Country profiles
df = povineq.get_cp(country="IDN")
df = povineq.get_cp_ki(country="IDN")

# Auxiliary tables
tables = povineq.get_aux()          # list available tables
gdp    = povineq.get_aux("gdp")    # fetch a specific table
cpi    = povineq.get_cpi()         # convenience wrapper

# API info
print(povineq.check_api())
print(povineq.get_versions())
```

## API Reference

| Function | Description |
|---|---|
| `get_stats()` | Poverty and inequality statistics |
| `get_wb()` | World Bank regional/global aggregates |
| `get_agg()` | Custom aggregates (FCV, etc.) |
| `get_cp()` | Country profile download |
| `get_cp_ki()` | Country profile key indicators |
| `get_aux(table)` | Auxiliary data tables |
| `get_countries()`, `get_regions()`, … | Per-table convenience wrappers |
| `check_api()` | API health check |
| `get_versions()` | Available data versions |
| `delete_cache()` | Clear the local cache directory |

## Development

```bash
git clone https://github.com/PIP-Technical-Team/povineq
cd povineq
env -u UV_INDEX -u UV_INDEX_URL -u UV_EXTRA_INDEX_URL UV_DEFAULT_INDEX=https://pypi.org/simple uv sync --locked --group dev
env -u UV_INDEX -u UV_INDEX_URL -u UV_EXTRA_INDEX_URL UV_DEFAULT_INDEX=https://pypi.org/simple uv run --locked pytest -m "not online"
```

Documentation and release tooling are uv dependency groups, not published
package extras. Use the locked public-PyPI commands below:

```bash
env -u UV_INDEX -u UV_INDEX_URL -u UV_EXTRA_INDEX_URL UV_DEFAULT_INDEX=https://pypi.org/simple uv sync --locked --no-default-groups --group docs
env -u UV_INDEX -u UV_INDEX_URL -u UV_EXTRA_INDEX_URL UV_DEFAULT_INDEX=https://pypi.org/simple uv sync --locked --no-default-groups --group release
```

## Release Process

Releases are tag-gated by `.github/workflows/publish.yml`. The validation job
requires the `vX.Y.Z` tag to match the version in `pyproject.toml`, builds and
checks the artifacts, and passes only those artifacts to the publish job.
Publishing uses PyPI trusted publishing through the self-service GitHub
environment `pypi`, which is restricted to protected `v*` tags. No PyPI token
is stored in the repository. The PyPI pending publisher must be registered
before the first release.

The PyPI trusted publisher must be registered with owner `PIP-Technical-Team`,
repository `povineq`, workflow `publish.yml`, and environment `pypi`.

## Data Source

World Bank [Poverty and Inequality Platform (PIP)](https://pip.worldbank.org/).
