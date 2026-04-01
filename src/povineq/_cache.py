"""Cache directory management for povineq."""

from __future__ import annotations

import functools
import shutil
from pathlib import Path

from loguru import logger
from platformdirs import user_cache_dir


@functools.lru_cache(maxsize=1)
def _cache_dir() -> Path:
    """Return the platform-appropriate cache directory for povineq.

    The result is cached after the first call so that subsequent requests
    do not issue redundant ``mkdir`` syscalls.

    Returns:
        :class:`~pathlib.Path` pointing to the cache directory.
        The directory is created if it does not already exist.
    """
    path = Path(user_cache_dir("povineq"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_cache() -> None:
    """Delete all cached HTTP responses.

    Removes the entire cache directory and re-creates an empty one so
    subsequent calls can start fresh.

    Example:
        >>> import povineq
        >>> povineq.delete_cache()
    """
    cache_path = _cache_dir()
    cached = list(cache_path.iterdir())
    if not cached:
        logger.info("Cache is empty. Nothing to delete.")
        return

    shutil.rmtree(cache_path)
    # Reset the lru_cache so the next call recreates the directory entry.
    if hasattr(_cache_dir, "cache_clear"):
        _cache_dir.cache_clear()
    cache_path.mkdir(parents=True, exist_ok=True)
    logger.info("All {} cached item(s) have been deleted.", len(cached))


def get_cache_info() -> dict[str, object]:
    """Return statistics about the current HTTP response cache.

    Returns:
        A dictionary with keys:

        - ``"path"``: absolute path to the cache directory.
        - ``"n_files"``: number of cached response files.
        - ``"total_bytes"``: total size of the cache in bytes.

    Example:
        >>> import povineq
        >>> info = povineq.get_cache_info()
        >>> print(info["n_files"])
    """
    cache_path = _cache_dir()
    files = list(cache_path.rglob("*"))
    files = [f for f in files if f.is_file()]
    total_bytes = sum(f.stat().st_size for f in files)
    return {
        "path": str(cache_path),
        "n_files": len(files),
        "total_bytes": total_bytes,
    }
