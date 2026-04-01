"""Request builder and executor for PIP API calls."""

from __future__ import annotations

import json
import re
import time

import httpx
from loguru import logger

from povineq._client import get_client
from povineq._constants import API_VERSION
from povineq._errors import PIPAPIError, PIPConnectionError, PIPRateLimitError

# Maximum seconds to wait on a rate-limit retry
_MAX_RETRY_SECONDS: float = 60.0
# Maximum number of rate-limit retries
_MAX_RATE_RETRIES: int = 3


def _extract_retry_after(response: httpx.Response) -> float:
    """Parse the wait time from a 429 rate-limit response body.

    The PIP API returns a message of the form:
    ``"Rate limit is exceeded. Try again in N seconds."``

    Args:
        response: The 429 HTTP response.

    Returns:
        Number of seconds to wait, or 0 if the message cannot be parsed.
    """
    try:
        body = response.json()
        message = body.get("message", "")
        match = re.search(r"Try again in (\d+(?:\.\d+)?)", message)
        if match:
            return float(match.group(1))
    except (ValueError, AttributeError, TypeError, KeyError):
        logger.debug("Could not parse retry-after body; falling back to default wait.")
    return 0.0


def _parse_api_error(response: httpx.Response) -> PIPAPIError:
    """Build a :class:`~povineq._errors.PIPAPIError` from an error response.

    Handles 502/504 gateway errors (HTML body) and structured PIP JSON errors.

    Args:
        response: The error HTTP response.

    Returns:
        A populated :class:`~povineq._errors.PIPAPIError`.
    """
    status = response.status_code

    # Gateway errors — body is HTML, not JSON
    if status in (502, 504):
        return PIPAPIError(status, error_message=response.reason_phrase)

    try:
        body = response.json()
        error_msg = ""
        details_msg = ""
        valid_values = ""

        if isinstance(body, dict):
            errors = body.get("error", [])
            if errors:
                error_msg = errors[0] if isinstance(errors, list) else str(errors)

            details = body.get("details", {})
            if isinstance(details, dict):
                for key in details:
                    msgs = details[key].get("msg", [])
                    if msgs:
                        details_msg = msgs[0]
                    valids = details[key].get("valid", [])
                    if valids:
                        valid_values = ", ".join(str(v) for v in valids)
                    break
            elif isinstance(details, list) and details:
                details_msg = details[0].get("msg", [""])[0] if details[0].get("msg") else ""

        return PIPAPIError(status, error_msg, details_msg, valid_values)
    except (ValueError, json.JSONDecodeError, KeyError, AttributeError, TypeError):
        return PIPAPIError(status, error_message=response.reason_phrase)


def build_and_execute(
    endpoint: str,
    params: dict[str, str],
    server: str | None = None,
    api_version: str = API_VERSION,
) -> httpx.Response:
    """Build a URL, execute a GET request, and handle rate-limit retries.

    Creates the full API URL from *endpoint* and *api_version*, then enters a
    retry loop of up to ``_MAX_RATE_RETRIES`` attempts. On a 429 response the
    loop sleeps for the number of seconds indicated in the response body (capped
    at ``_MAX_RETRY_SECONDS``) before the next attempt.

    Args:
        endpoint: PIP API endpoint path segment (e.g. ``"pip"``).
        params: Query-string parameters as a flat string dict.
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.
        api_version: API version path segment (default ``"v1"``).

    Returns:
        The successful :class:`httpx.Response`.

    Raises:
        PIPRateLimitError: When rate limit is exceeded and all retries are
            exhausted. The exception carries the recommended wait time.
        PIPAPIError: When the API returns a 4xx or 5xx error other than 429,
            including structured JSON error messages from the PIP API.
        PIPConnectionError: When the network is unreachable or a transport-level
            error occurs (timeout, DNS failure, TLS error, etc.).
    """
    url = f"/{api_version}/{endpoint}"

    # Create the client once outside the retry loop to reuse the connection pool.
    client = get_client(server)
    for attempt in range(_MAX_RATE_RETRIES + 1):
        try:
            logger.debug("GET request", url=url, params=params)
            response = client.get(url, params=params)
        except httpx.RequestError as exc:
            raise PIPConnectionError(
                "Cannot reach the PIP API. Check your internet connection."
            ) from exc

        if response.status_code == 429:
            wait = _extract_retry_after(response)
            wait = min(wait, _MAX_RETRY_SECONDS)

            if attempt >= _MAX_RATE_RETRIES:
                raise PIPRateLimitError(wait)

            logger.warning("Rate limit hit", wait_seconds=round(wait), attempt=attempt + 1)
            time.sleep(wait if wait > 0 else 1)
            continue

        if response.is_error:
            raise _parse_api_error(response)

        return response

    # Should never reach here, but satisfies the type checker
    raise PIPRateLimitError(0)
