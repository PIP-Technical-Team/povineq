---
date: 2026-04-01
title: "hishel >=1.0 removed CacheTransport/FileStorage/Controller API"
category: "build-errors"
language: "Python"
tags: [hishel, httpx, caching, http-client, breaking-change]
root-cause: "hishel dropped its entire public caching API in v1.0; the classes CacheTransport, FileStorage, and Controller no longer exist."
severity: "P2"
---

# hishel >=1.0 Removed CacheTransport / FileStorage / Controller

## Problem

Code that used `hishel` for caching HTTP responses (commonly paired with `httpx`) would
fail at import time with:

```
ImportError: cannot import name 'CacheTransport' from 'hishel'
ImportError: cannot import name 'FileStorage' from 'hishel'
ImportError: cannot import name 'Controller' from 'hishel'
```

No deprecation warning is raised; the classes simply no longer exist in hishel >= 1.0.

## Root Cause

The `hishel` library made a major API redesign between pre-1.0 and the 1.0 stable
release, removing the thin transport-wrapper pattern entirely. Pinned or loose
dependencies (`hishel>=0.x`) silently upgrade to 1.0 in fresh environments or after
`uv sync`/`pip install --upgrade`.

## Solution

Remove `hishel` entirely and implement retry logic directly via
`httpx.HTTPTransport(retries=N)`. This handles transient connection errors without
the disk I/O overhead of HTTP caching:

**Before (broken with hishel >= 1.0):**
```python
import hishel

storage = hishel.FileStorage(base_path=cache_dir)
controller = hishel.Controller(cacheable_status_codes=[200])
transport = hishel.CacheTransport(
    transport=httpx.HTTPTransport(retries=3),
    storage=storage,
    controller=controller,
)
client = httpx.Client(transport=transport)
```

**After (works with any httpx >= 0.27):**
```python
import httpx

client = httpx.Client(
    base_url=base_url,
    transport=httpx.HTTPTransport(retries=3),
    headers={"User-Agent": USER_AGENT},
    timeout=60.0,
)
```

If true HTTP-layer caching is required, pin `hishel<1.0` until the new API is
understood, or switch to `httpx-cache` which has a stable interface.

## Prevention

- Pin `hishel` to `<1.0` in `pyproject.toml` if you need caching: `hishel>=0.0.30,<1.0`
- Prefer `httpx.HTTPTransport(retries=N)` for retry-only use cases — no extra dependency
- Add `hishel` to the list of packages to monitor for major version bumps in CI

## Related

- httpx docs on transports: https://www.python-httpx.org/advanced/transports/
- hishel changelog: https://hishel.com/changelog/
