# Caching and Performance

`povineq` currently uses HTTP connection pooling and transport retries. The
cache-directory helpers are retained for local cache management, but the active
HTTP client does not persist or replay API responses.

---

## How the Cache Works

The cache directory is platform-appropriate:

| OS | Default location |
|---|---|
| macOS | `~/Library/Caches/povineq/` |
| Linux | `~/.cache/povineq/` |
| Windows | `%LOCALAPPDATA%\povineq\Cache\` |

The current request layer does not write response files to this directory.

---

## Inspecting the Cache

Use `get_cache_info()` to see how many files are in the cache directory and how much disk space
they use:

```python
import povineq

info = povineq.get_cache_info()
print(info["path"])        # path to the cache directory
print(info["n_files"])     # number of files in the cache directory
print(info["total_bytes"]) # total size in bytes
```

---

## Clearing the Cache

Delete all files in the managed cache directory with `delete_cache()`:

```python
import povineq

povineq.delete_cache()
```

This removes the managed cache directory and recreates an empty one. The active
HTTP client does not currently write response files there.

!!! tip
    Use the `version` or `release_version` parameter in `get_stats()` and other
    functions to request a specific PIP data release.

---

## Request Versions

To request a specific data release, pin `release_version`:

```python
import povineq

df = povineq.get_stats(
    country="IDN",
    release_version="20240101",
)
```

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

See [`povineq._cache`](../reference/internal/cache.md) for the full documentation of
`delete_cache()` and `get_cache_info()`.
