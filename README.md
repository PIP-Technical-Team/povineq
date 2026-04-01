# povineq

Python wrapper for the [World Bank PIP API](https://pip.worldbank.org/).
Mirrors the functionality of the [`pipr`](https://github.com/worldbank/pipr) R package.

## Installation

```bash
pip install povineq
# with optional polars support
pip install "povineq[polars]"
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
| `delete_cache()` | Clear the HTTP response cache |

## Development

```bash
git clone https://github.com/PIP-Technical-Team/povineq
cd povineq
uv sync --extra dev
uv run pytest -m "not online"
```

## Data Source

World Bank [Poverty and Inequality Platform (PIP)](https://pip.worldbank.org/).
