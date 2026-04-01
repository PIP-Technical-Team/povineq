---
date: 2026-04-01
title: "pandas inplace=True silently returns None, causing downstream NoneType errors"
category: "bugs"
language: "Python"
tags: [pandas, inplace, dataframe, NoneType, silent-bug]
root-cause: "pandas methods with inplace=True return None, not the modified DataFrame. Assigning the result or chaining it produces a NoneType that silently passes through until much later."
severity: "P1"
---

# pandas `inplace=True` Silently Returns `None`

## Problem

Code using `inplace=True` on pandas DataFrame methods (e.g., `rename`, `drop`,
`set_index`, `sort_values`) stores `None` in the variable when the result is assigned
or chained. This produces a `NoneType` object that persists silently until a later
operation fails with:

```
AttributeError: 'NoneType' object has no attribute 'columns'
AttributeError: 'NoneType' object has no attribute 'merge'
```

The symptom appears far from the source of the bug, making it hard to diagnose.

**Concrete example that caused a bug in this codebase:**
```python
df = df.rename(columns=renames, inplace=True)  # df is now None!
df.merge(other, on="country_code")             # AttributeError here — far from root cause
```

## Root Cause

The `inplace=True` parameter mutates the object in-place **and** returns `None`.
Assigning `None` to `df` overwrites the reference to the valid DataFrame with `None`.
This is a well-known pandas design quirk — `inplace=True` was intended for use
*without* assignment.

## Solution

Never use `inplace=True`. Always reassign:

**Before (broken):**
```python
df.rename(columns=renames, inplace=True)
df.drop(columns=["tmp"], inplace=True)
df.sort_values("year", inplace=True)
```

**After (correct):**
```python
df = df.rename(columns=renames)
df = df.drop(columns=["tmp"])
df = df.sort_values("year")
```

Note: the reassignment is a cheap reference update — pandas does **not** copy the
DataFrame.  If memory is a concern, the extra name binding is negligible compared
to the eliminated bug risk.

## Prevention

- Enable the `pandas-vet` ruff plugin rules (e.g., `PD002: inplace=True should
  be avoided`) in `pyproject.toml`:
  ```toml
  [tool.ruff.lint]
  select = ["PD"]
  ```
- Never write `inplace=True` — there is no situation where it is safer than reassignment.
- The `cg-skill-python-best-practices` skill lists this as a pandas anti-pattern.

## Related

- pandas docs: https://pandas.pydata.org/docs/user_guide/indexing.html#returning-a-view-versus-a-copy
- ruff PD002 rule: https://docs.astral.sh/ruff/rules/pandas-use-of-inplace-argument/
