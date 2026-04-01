# Caching and Performance

`povineq` caches HTTP responses on disk so that repeated calls to the PIP API
return instantly without hitting the network. This page explains how the cache
works and how to manage it.

---

## How the Cache Works

Every successful API response is stored in a platform-appropriate cache
directory:

| OS | Default location |
|---|---|
| macOS | `~/Library/Caches/povineq/` |
| Linux | `~/.cache/povineq/` |
| Windows | `%LOCALAPPDATA%\povineq\Cache\` |

The cache key is derived from the full request URL (including all query
parameters). If you call the same function with the same arguments twice, the
second call reads from disk — no network request is made.

---

## Inspecting the Cache

Use `get_cache_info()` to see how many files are cached and how much disk space
they use:

```python
import povineq

info = povineq.get_cache_info()
print(info["path"])        # path to the cache directory
print(info["n_files"])     # number of cached responses
print(info["total_bytes"]) # total size in bytes
```

---

## Clearing the Cache

Delete all cached responses with `delete_cache()`:

```python
import povineq

povineq.delete_cache()
```

This removes the entire cache directory and recreates an empty one. The next
API call will fetch fresh data from the server.

!!! tip
    Clear the cache when a new PIP data version is released to ensure you are
    working with the latest estimates. You can also pin a specific version using
    the `version` parameter in `get_stats()` and other functions.

---

## Bypassing the Cache

To force a fresh request without clearing the entire cache, pin a specific
`release_version`:

```python
import povineq

# Forces a new request because the version string is part of the cache key
df = povineq.get_stats(
    country="IDN",
    release_version="20240101",
)
```

Alternatively, `delete_cache()` before the call.

---

## Performance Tips

- **Batch country queries**: fetching `get_stats(country=["IDN", "IND", "BRA"])`
  is one API call; calling `get_stats(country="IDN")` three times is three
  calls.
- **Use `fill_gaps=True` once**: fetching gap-filled data for all countries in
  one call is faster than looping over countries.
- **Reuse sessions**: `povineq` uses `httpx` with connection pooling. Within a
  single Python process, connections are reused automatically.
- **Store auxiliary tables**: if you call `get_gdp()` and `get_cpi()` multiple
  times in a session, store them with `assign_tb=True` to avoid repeated
  deserialization.

---

## API Reference

See [`povineq._cache`](../reference/cache.md) for the full documentation of
`delete_cache()` and `get_cache_info()`.
