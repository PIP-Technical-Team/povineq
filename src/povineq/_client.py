"""HTTP client setup using httpx + hishel (caching) with retry logic."""

from __future__ import annotations

import os

import hishel
import httpx

from povineq._cache import _cache_dir
from povineq._constants import ENV_DEV_URL, ENV_QA_URL, PROD_URL, USER_AGENT


def select_base_url(server: str | None) -> str:
    """Return the API base URL for the given server target.

    Args:
        server: One of ``"prod"``, ``"qa"``, ``"dev"``, or ``None`` (defaults to prod).

    Returns:
        Base URL string without a trailing slash.

    Raises:
        ValueError: If *server* is not one of the accepted values.
        EnvironmentError: If qa/dev URL environment variable is not set.
    """
    if server is None or server == "prod":
        return PROD_URL

    if server not in ("qa", "dev"):
        raise ValueError(f"server must be 'prod', 'qa', or 'dev', got {server!r}")

    env_var = ENV_QA_URL if server == "qa" else ENV_DEV_URL
    url = os.environ.get(env_var, "")
    if not url:
        raise OSError(
            f"'{server}' URL not found. Set the {env_var!r} environment variable."
        )
    return url


def get_client(server: str | None = None) -> httpx.Client:
    """Return a configured httpx client with caching and automatic retry.

    The client uses :mod:`hishel` for RFC 7234 HTTP caching and retries up to
    3 times on transient connection errors (not on rate limits — those are
    handled separately by the request layer).

    Args:
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.

    Returns:
        A ready-to-use :class:`httpx.Client`.
    """
    base_url = select_base_url(server)
    storage = hishel.FileStorage(base_path=_cache_dir())
    controller = hishel.Controller(allow_stale=True)
    transport = hishel.CacheTransport(
        transport=httpx.HTTPTransport(retries=3),
        storage=storage,
        controller=controller,
    )
    return httpx.Client(
        base_url=base_url,
        transport=transport,
        headers={"User-Agent": USER_AGENT},
        timeout=60.0,
    )
