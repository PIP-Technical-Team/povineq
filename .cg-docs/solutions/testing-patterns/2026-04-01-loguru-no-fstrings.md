---
date: 2026-04-01
title: "loguru: avoid f-strings in log calls (defeats lazy evaluation)"
category: "testing-patterns"
language: "Python"
tags: [loguru, logging, performance, f-string, structured-logging]
root-cause: "F-strings are eagerly evaluated at call site, even when the log level is disabled. loguru's structured-argument syntax is lazy and also searchable."
severity: "P2"
---

# loguru: Avoid f-strings in Log Calls

## Problem

Calls like `logger.debug(f"Processing {len(data)} records")` pass a pre-formatted
string to loguru. If the `DEBUG` level is disabled in production:

1. The f-string is **still evaluated** — wasting CPU, especially inside loops.
2. Structured log sinks (JSON, Datadog, Loki) cannot extract the field values as
   separate searchable keys.
3. Large objects are `repr()`-ed eagerly, causing unnecessary memory allocation.

## Root Cause

Python evaluates f-strings at the call site **before** the function is invoked.
loguru cannot intercept this; by the time it sees the message string, the interpolation
is already done and the level-gate check is moot.

## Solution

Use loguru's structured keyword-argument syntax instead of f-strings:

**Before (f-string — eager, non-searchable):**
```python
logger.debug(f"Fetching {table!r} with params {params}")
logger.info(f"Got {len(records)} rows for country {country}")
logger.warning(f"Rate limit hit; waiting {wait:.1f}s")
```

**After (lazy, structured):**
```python
logger.debug("Fetching table", table=table, params=params)
logger.info("Got rows", n_rows=len(records), country=country)
logger.warning("Rate limit hit; waiting", wait_seconds=wait)
```

For messages where the format string is truly needed (e.g., `{}` placeholders),
loguru lazily interpolates only when the level is active:

```python
logger.debug("Fetching {table!r} with params {params}", table=table, params=params)
```

## Prevention

- Add a ruff rule to `pyproject.toml` if available, or search for `f"` inside
  `logger.` calls during code review.
- The `cg-skill-python-best-practices` skill lists loguru structured args as
  **mandatory**. Reference it when reviewing `.py` files.
- In tests using `loguru`'s `caplog`/`capfd`, structured-arg messages are easier
  to assert on because you can check the `record.extra` dict rather than parsing
  a formatted string.

## Related

- loguru docs — lazy evaluation: https://loguru.readthedocs.io/en/stable/overview.html#structured-logging-as-needed
- `.github/skills/cg-skill-python-best-practices/SKILL.md` — Python logging conventions
