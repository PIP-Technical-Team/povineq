"""HTTP client setup using httpx with connection-pool reuse and retry logic."""

from __future__ import annotations

import os

import httpx

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
    """Return a configured httpx client with connection-pool reuse and automatic retry.

    Retries up to 3 times on transient connection errors (not on rate limits —
    those are handled separately by the request layer).

    Args:
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.

    Returns:
        A ready-to-use :class:`httpx.Client`.
    """
    base_url = select_base_url(server)
    return httpx.Client(
        base_url=base_url,
        transport=httpx.HTTPTransport(retries=3),
        headers={"User-Agent": USER_AGENT},
        timeout=60.0,
    )
