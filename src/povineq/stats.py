"""Core poverty and inequality statistics functions."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from loguru import logger

from povineq._constants import API_VERSION, ENDPOINT_PIP, ENDPOINT_PIP_GRP
from povineq._request import build_and_execute
from povineq._response import PIPResponse, parse_response
from povineq._validation import AggParams, StatsParams


def get_stats(
    country: str | list[str] = "all",
    year: str | int | list[int] = "all",
    povline: float | None = None,
    popshare: float | None = None,
    fill_gaps: bool = False,
    nowcast: bool = False,
    subgroup: str | None = None,
    welfare_type: str = "all",
    reporting_level: str = "all",
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "arrow",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Get poverty and inequality statistics from the PIP API.

    This is the primary function for querying household survey-based poverty
    and inequality estimates. It mirrors ``pipr::get_stats()``.

    Args:
        country: ISO3 country code(s) or ``"all"``.
        year: Survey year(s) or ``"all"``.
        povline: Poverty line in 2017 PPP USD per day.
        popshare: Proportion of the population below the poverty line.
            When set, *povline* is ignored.
        fill_gaps: If ``True``, interpolate/extrapolate values for years
            without survey data.
        nowcast: If ``True``, include nowcast estimates (implies
            ``fill_gaps=True``).
        subgroup: Pre-defined aggregation. Either ``"wb_regions"`` or
            ``"none"``. When set, routes to the ``pip-grp`` endpoint.
        welfare_type: Welfare concept — ``"all"``, ``"income"``, or
            ``"consumption"``.
        reporting_level: Geographic level — ``"all"``, ``"national"``,
            ``"urban"``, or ``"rural"``.
        version: Data version string (see :func:`~povineq.info.get_versions`).
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version (only ``"v1"`` currently).
        format: Response format — ``"arrow"`` (default), ``"json"``, or
            ``"csv"``.
        simplify: If ``True`` (default), return a DataFrame. If ``False``,
            return a :class:`~povineq._response.PIPResponse` wrapper.
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        A :class:`~pandas.DataFrame` when *simplify* is ``True``, or a
        :class:`~povineq._response.PIPResponse` when *simplify* is ``False``.

    Raises:
        PIPValidationError: If parameter values are invalid.
        PIPAPIError: If the API returns a structured error response.
        PIPRateLimitError: If the rate limit is exceeded after retries.
        PIPConnectionError: If the network is unreachable.

    Example:
        >>> import povineq
        >>> df = povineq.get_stats(country="AGO", year=2000)
        >>> df = povineq.get_stats(country="all", year="all", fill_gaps=True)
        >>> df = povineq.get_stats(country="all", subgroup="wb_regions")
    """
    logger.debug(
        "get_stats",
        country=country,
        year=year,
        povline=povline,
        popshare=popshare,
        fill_gaps=fill_gaps,
        nowcast=nowcast,
        subgroup=subgroup,
    )

    # Validate and apply business rules via pydantic
    params = StatsParams(
        country=country,
        year=year,
        povline=povline,
        popshare=popshare,
        fill_gaps=fill_gaps,
        nowcast=nowcast,
        subgroup=subgroup,
        welfare_type=welfare_type,
        reporting_level=reporting_level,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        api_version=api_version,
        format=format,
    )

    # Route endpoint
    if params.subgroup is not None:
        endpoint = ENDPOINT_PIP_GRP
        group_by = "wb" if params.subgroup == "wb_regions" else params.subgroup
    else:
        endpoint = ENDPOINT_PIP
        group_by = None

    # Build query params (exclude subgroup; use group_by instead)
    query = params.to_query_params()
    query.pop("subgroup", None)
    query.pop("nowcast", None)  # nowcast is not an API query param
    if group_by is not None:
        query["group_by"] = group_by

    response = build_and_execute(endpoint, query, server=server, api_version=api_version)

    out = parse_response(response, simplify=simplify, dataframe_type=dataframe_type)

    # When fill_gaps=False (and simplify=True) filter out nowcast rows
    # pipr does this because estimate_type is only returned when fill_gaps=True
    if params.nowcast is False and simplify and isinstance(out, pd.DataFrame):
        if "estimate_type" in out.columns:
            out = out[~out["estimate_type"].str.contains("nowcast", na=False)].copy()

    return out


def get_wb(
    year: str | int | list[int] = "all",
    povline: float | None = None,
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Get World Bank regional and global aggregate statistics.

    Shorthand for ``get_stats(subgroup="wb_regions")``.
    Mirrors ``pipr::get_wb()``.

    Args:
        year: Year(s) or ``"all"``.
        povline: Poverty line in 2017 PPP USD per day.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        format: Response format — ``"json"`` (default) or ``"csv"``.
        simplify: If ``True`` (default), return a DataFrame.
        server: Server target.
        dataframe_type: ``"pandas"`` or ``"polars"``.

    Returns:
        A DataFrame of WB regional/global aggregates.

    Example:
        >>> import povineq
        >>> df = povineq.get_wb()
    """
    query: dict[str, str] = {}
    if year != "all":
        query["year"] = ",".join(str(y) for y in year) if isinstance(year, list) else str(year)
    else:
        query["year"] = "all"

    if povline is not None:
        query["povline"] = str(povline)
    if version is not None:
        query["version"] = version
    if ppp_version is not None:
        query["ppp_version"] = str(ppp_version)
    if release_version is not None:
        query["release_version"] = release_version
    query["format"] = format
    query["group_by"] = "wb"

    response = build_and_execute(
        ENDPOINT_PIP_GRP, query, server=server, api_version=api_version
    )
    return parse_response(response, simplify=simplify, dataframe_type=dataframe_type)


def get_agg(
    year: str | int | list[int] = "all",
    povline: float | None = None,
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    aggregate: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Get custom aggregate statistics (FCV, regional, vintage, etc.).

    Mirrors ``pipr::get_agg()``.

    Args:
        year: Year(s) or ``"all"``.
        povline: Poverty line in 2017 PPP USD per day.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        aggregate: Aggregate name (e.g. ``"fcv"``).
        api_version: API version.
        format: Response format — ``"json"`` (default) or ``"csv"``.
        simplify: If ``True`` (default), return a DataFrame.
        server: Server target.
        dataframe_type: ``"pandas"`` or ``"polars"``.

    Returns:
        A DataFrame of custom aggregate statistics.

    Example:
        >>> import povineq
        >>> df = povineq.get_agg(aggregate="fcv", server="qa")
    """
    params = AggParams(
        year=year,
        povline=povline,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        aggregate=aggregate,
        api_version=api_version,
        format=format,
    )

    query = params.to_query_params()
    query.pop("api_version", None)

    response = build_and_execute(
        ENDPOINT_PIP_GRP, query, server=server, api_version=api_version
    )
    return parse_response(response, simplify=simplify, dataframe_type=dataframe_type)
