# Country Profiles

This tutorial covers the three country-profile functions:

| Function | Description |
|---|---|
| `get_cp()` | Download a full country profile dataset |
| `get_cp_ki()` | Country profile key indicators (metadata-rich) |
| `unnest_ki()` | Flatten nested key-indicator rows into one row per indicator |

---

## `get_cp()` — Country profile download

`get_cp()` downloads the full country profile dataset: a comprehensive set of
poverty and inequality estimates computed at multiple poverty lines for one or
more countries.

### Basic usage

```python
import povineq

# Single country
df = povineq.get_cp(country="AGO")

# Multiple countries
df = povineq.get_cp(country=["IDN", "IND"])

# All countries
df = povineq.get_cp()
```

### Custom poverty line

The default poverty line is $2.15/day (2017 PPP). Supply your own:

```python
df = povineq.get_cp(country="BRA", povline=3.65)
```

### PPP year

Switch between PPP base years:

```python
# 2011 PPP
df = povineq.get_cp(country="AGO", ppp_version=2011)

# 2017 PPP (default)
df = povineq.get_cp(country="AGO", ppp_version=2017)
```

### Polars output

```python
df = povineq.get_cp(country="IDN", dataframe_type="polars")
```

---

## `get_cp_ki()` — Key indicators

`get_cp_ki()` returns a condensed set of key indicators per country. Each row
contains a nested structure with indicator values across multiple years.

```python
import povineq

df = povineq.get_cp_ki(country="IDN")
print(df.columns.tolist())
```

### Unnesting key indicators

The nested columns can be hard to work with directly. Use `unnest_ki()` to
flatten the result into one row per country-indicator:

```python
import povineq

df_ki = povineq.get_cp_ki(country="IDN")
df_flat = povineq.unnest_ki(df_ki)
print(df_flat.head())
```

Multiple countries:

```python
df_ki = povineq.get_cp_ki(country=["IDN", "IND", "BRA"])
df_flat = povineq.unnest_ki(df_ki)
```

---

## API Reference

See [`povineq.country_profiles`](../reference/country_profiles.md) for the
full parameter documentation.
