# Auxiliary Data

The PIP API exposes a set of auxiliary data tables — GDP, CPI, PPP, population,
survey metadata, and more. `povineq` provides a general `get_aux()` function
plus per-table convenience wrappers.

| Function | Table |
|---|---|
| `get_aux(table)` | Any auxiliary table by name |
| `get_countries()` | Country list |
| `get_regions()` | Region list |
| `get_gdp()` | GDP data |
| `get_cpi()` | CPI data |
| `get_ppp()` | PPP data |
| `get_pop()` | Total population |
| `get_pop_region()` | Population by region |
| `get_incgrp_coverage()` | Income group coverage |
| `get_region_coverage()` | Regional coverage |
| `get_survey_means()` | Survey mean welfare |
| `get_interpolated_means()` | Interpolated means |
| `get_hfce()` | Household final consumption expenditure |
| `get_dictionary()` | Data dictionary |
| `display_aux()` | Print auxiliary data stored in memory |
| `call_aux()` | Retrieve auxiliary data from the in-memory store |

---

## Listing Available Tables

Call `get_aux()` with no arguments to see which tables are available:

```python
import povineq

tables = povineq.get_aux()
print(tables)   # ['countries', 'regions', 'gdp', 'cpi', ...]
```

---

## Fetching a Specific Table

Pass the table name to `get_aux()`:

```python
gdp = povineq.get_aux("gdp")
cpi = povineq.get_aux("cpi")
```

---

## Convenience Wrappers

Each table has its own function:

```python
import povineq

countries = povineq.get_countries()
regions   = povineq.get_regions()
gdp       = povineq.get_gdp()
cpi       = povineq.get_cpi()
ppp       = povineq.get_ppp()
pop       = povineq.get_pop()
```

---

## Storing Tables in Memory

Use `assign_tb=True` to fetch a table and keep it in the in-memory store for
fast subsequent access — useful when running many calls in the same session:

```python
import povineq

# Fetch and store under the table's own name ("gdp")
povineq.get_aux("gdp", assign_tb=True)

# Fetch and store under a custom name
povineq.get_aux("gdp", assign_tb="my_gdp")
```

Retrieve a stored table with `call_aux()`:

```python
gdp = povineq.call_aux("gdp")
```

List what is currently stored:

```python
povineq.display_aux()
```

---

## Polars Output

All `get_aux()` calls accept `dataframe_type`:

```python
gdp = povineq.get_aux("gdp", dataframe_type="polars")
```

---

## Version Pinning

Pin a specific data version for reproducible results:

```python
gdp = povineq.get_aux("gdp", version="20230919_2017_01_02_PROD")
```

---

## API Reference

See [`povineq.auxiliary`](../reference/auxiliary.md) for the full parameter
documentation.
