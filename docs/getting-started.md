# Getting Started

This page walks you through installing `povineq`, making your first API call,
and understanding the result.

---

## Requirements

- Python 3.10 or newer
- An internet connection for live API calls (cached responses work offline)

---

## Installation

Install the package from PyPI:

!!! note "Pre-release"
    `povineq` is in active development. If `pip install povineq` fails,
    install directly from source:
    `pip install git+https://github.com/PIP-Technical-Team/povineq.git`

```bash
pip install povineq
```

For [polars](https://pola.rs/) support alongside the default pandas output:

```bash
pip install "povineq[polars]"
```

---

## Your First Query

Import `povineq` and call `get_stats()` to fetch poverty estimates for one
country:

```python
import povineq

df = povineq.get_stats(country="AGO", year=2000)
print(df)
```

The function returns a `pandas.DataFrame` by default. Each row is one
estimate — usually one survey — and the columns include headcount ratio, poverty
gap, Gini coefficient, mean welfare, and more.

---

## Exploring All Countries

Omit `country` and `year` to get every available estimate:

```python
df = povineq.get_stats()
print(df.shape)   # hundreds of rows, one per survey
```

---

## Gap-Filled Estimates

By default, `get_stats()` returns only survey years. Set `fill_gaps=True` to
interpolate and extrapolate estimates for years without surveys:

```python
df = povineq.get_stats(fill_gaps=True)
```

This is equivalent to what `pipr::get_stats(fill_gaps = TRUE)` does in R.

---

## Switching to Polars

Every function that returns a DataFrame accepts a `dataframe_type` argument:

```python
import povineq

df = povineq.get_stats(country="IDN", dataframe_type="polars")
print(type(df))   # <class 'polars.DataFrame'>
```

Polars must be installed separately — see Installation above.

---

## Using `simplify=False` for the Raw Response

By default (`simplify=True`) functions return a plain DataFrame. Pass
`simplify=False` to receive a `PIPResponse` wrapper that exposes the HTTP
response, headers, and raw body alongside the parsed data:

```python
import povineq

resp = povineq.get_stats(country="AGO", year=2000, simplify=False)
print(resp.status_code)
print(resp.elapsed)
df = resp.to_dataframe()
```

---

## Checking the API

Verify that the PIP API is reachable before running a batch job:

```python
import povineq

status = povineq.check_api()
print(status)
```

---

## Error Handling

`povineq` raises typed exceptions so you can catch only what you expect:

```python
from povineq import PIPAPIError, PIPConnectionError, PIPRateLimitError, PIPValidationError

try:
    df = povineq.get_stats(country="XYZ")
except PIPValidationError as e:
    print("Bad parameters:", e)
except PIPAPIError as e:
    print("API error:", e.status_code, e.message)
except PIPConnectionError:
    print("Could not reach the PIP API")
```

All exception types are documented in the [API Reference](reference/internal/errors.md).

---

## Next Steps

- [Poverty Statistics tutorial](tutorials/poverty-statistics.md) — `get_stats`,
  `get_wb`, `get_agg` in depth.
- [Country Profiles tutorial](tutorials/country-profiles.md) — `get_cp`,
  `get_cp_ki`, `unnest_ki`.
- [Auxiliary Data tutorial](tutorials/auxiliary-data.md) — `get_aux` and all
  convenience wrappers.
- [Caching tutorial](tutorials/caching.md) — how the cache works and how to
  manage it.
