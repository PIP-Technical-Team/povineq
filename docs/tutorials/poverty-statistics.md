# Poverty Statistics

This tutorial covers the three main statistics functions:

| Function | Description |
|---|---|
| `get_stats()` | Survey-based poverty & inequality estimates |
| `get_wb()` | World Bank regional and global aggregates |
| `get_agg()` | Custom group aggregates (FCV, etc.) |

---

## `get_stats()` — Survey-level estimates

`get_stats()` is the primary function. It queries the PIP API for
household-survey-based poverty and inequality estimates.

### Basic usage

```python
import povineq

# Single country, single year
df = povineq.get_stats(country="AGO", year=2000)

# Multiple countries
df = povineq.get_stats(country=["IDN", "IND", "BRA"])

# All countries, all years
df = povineq.get_stats()
```

### Poverty lines

By default the API uses the $2.15/day international poverty line (2017 PPP).
You can supply a custom poverty line:

```python
# $3.65/day line
df = povineq.get_stats(povline=3.65)

# Or find the line that yields a given headcount (popshare)
df = povineq.get_stats(country="IDN", year=2019, popshare=0.50)
```

!!! note
    When `popshare` is set, the `povline` parameter is ignored.

### Gap-filling

Household surveys are conducted irregularly. Use `fill_gaps=True` to
interpolate and extrapolate estimates for every year:

```python
df = povineq.get_stats(country="BRA", fill_gaps=True)
```

### Welfare type and reporting level

Filter by welfare concept and geographic level:

```python
# Income-based estimates only
df = povineq.get_stats(welfare_type="income")

# Urban estimates only
df = povineq.get_stats(reporting_level="urban")
```

### WB-region sub-groups

Route the query through the `pip-grp` endpoint to get regional breakdowns
within the standard WB country groups:

```python
df = povineq.get_stats(subgroup="wb_regions")
```

### Polars output

```python
df = povineq.get_stats(country="IDN", year=2019, dataframe_type="polars")
```

---

## `get_wb()` — World Bank aggregates

`get_wb()` returns the official WB regional and global poverty aggregates
(computed from the `pip-grp` endpoint).

```python
# All years, all regions
df = povineq.get_wb()

# Specific year
df = povineq.get_wb(year=2019)

# Custom poverty line
df = povineq.get_wb(povline=3.65)
```

---

## `get_agg()` — Custom group aggregates

`get_agg()` fetches aggregated estimates for pre-defined country groups such
as Fragile and Conflict-affected States (FCV):

```python
# Fragile and conflict-affected states
df = povineq.get_agg(aggregate="fcv")
```

Check the API for the full list of available aggregates:

```python
import povineq

info = povineq.get_pip_info()
print(info)
```

---

## API Reference

See [`povineq.stats`](../reference/stats.md) for the full parameter
documentation.
