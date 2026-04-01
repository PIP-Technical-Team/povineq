"""API information, version, and health-check functions."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from loguru import logger

from povineq._constants import (
    API_VERSION,
    ENDPOINT_HEALTH_CHECK,
    ENDPOINT_PIP_INFO,
    ENDPOINT_VERSIONS,
)
from povineq._request import build_and_execute
from povineq._response import parse_response


def check_api(
    api_version: str = API_VERSION,
    server: str | None = None,
) -> dict:
    """Test connectivity to the PIP API.

    Hits the ``health-check`` endpoint and returns the parsed response.
    Mirrors ``pipr::check_api()``.

    Args:
        api_version: API version (only ``"v1"`` currently).
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.

    Returns:
        A dict with the health-check response from the API.

    Raises:
        PIPConnectionError: If the network is unreachable.
        PIPAPIError: If the health-check endpoint returns an error.

    Example:
        >>> import povineq
        >>> status = povineq.check_api()
    """
    logger.debug("check_api()")
    response = build_and_execute(ENDPOINT_HEALTH_CHECK, {}, server=server, api_version=api_version)
    result = parse_response(response, simplify=False, is_raw=True)
    if isinstance(result, dict):
        return result
    return {"status": response.status_code}


def get_versions(
    api_version: str = API_VERSION,
    server: str | None = None,
    simplify: bool = True,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | dict | list:
    """List available data versions.

    Mirrors ``pipr::get_versions()``.

    Args:
        api_version: API version (only ``"v1"`` currently).
        server: Server target.
        simplify: If ``True`` (default), return a DataFrame.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        A DataFrame of available versions when *simplify* is ``True``,
        or the raw dict/list otherwise.

    Example:
        >>> import povineq
        >>> df = povineq.get_versions()
    """
    logger.debug("get_versions()")
    response = build_and_execute(ENDPOINT_VERSIONS, {}, server=server, api_version=api_version)
    return parse_response(response, simplify=simplify, dataframe_type=dataframe_type)


def get_pip_info(
    api_version: str = API_VERSION,
    server: str | None = None,
) -> dict:
    """Get metadata about the PIP API.

    Mirrors ``pipr::get_pip_info()``.

    Args:
        api_version: API version (only ``"v1"`` currently).
        server: Server target.

    Returns:
        A dict with API metadata (version, endpoints, etc.).

    Example:
        >>> import povineq
        >>> info = povineq.get_pip_info()
    """
    logger.debug("get_pip_info()")
    response = build_and_execute(ENDPOINT_PIP_INFO, {}, server=server, api_version=api_version)
    result = parse_response(response, simplify=False, is_raw=True)
    if isinstance(result, dict):
        return result
    return {}
