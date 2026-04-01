"""Country profile download and key indicator functions."""

from __future__ import annotations

import json
from typing import Literal

import pandas as pd
from loguru import logger

from povineq._constants import (
    API_VERSION,
    ENDPOINT_CP_DOWNLOAD,
    ENDPOINT_CP_KEY_INDICATORS,
)
from povineq._request import build_and_execute
from povineq._response import PIPResponse, parse_response
from povineq._validation import CpKiParams, CpParams


def get_cp(
    country: str | list[str] = "all",
    povline: float | None = 2.15,
    version: str | None = None,
    ppp_version: int = 2017,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    fmt: str = "arrow",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Download country profile data.

    Mirrors ``pipr::get_cp()``.

    Args:
        country: ISO3 country code(s) or ``"all"``.
        povline: Poverty line in 2017 PPP USD per day (default 2.15).
            When ``ppp_version=2011`` and *povline* is ``None``,
            defaults to 1.9.
        version: Data version string.
        ppp_version: PPP base year (default 2017).
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        fmt: Response format — ``"arrow"`` (default), ``"json"``,
            or ``"csv"``.
        simplify: If ``True`` (default), return a DataFrame.
        server: Server target — ``None``/``"prod"``, ``"qa"``, or ``"dev"``.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        A DataFrame of country profile data.

    Example:
        >>> import povineq
        >>> df = povineq.get_cp(country="AGO")
        >>> df_all = povineq.get_cp()
    """
    logger.debug("get_cp", country=country, povline=povline, ppp_version=ppp_version)

    params = CpParams(
        country=country,
        povline=povline,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        api_version=api_version,
        format=fmt,
    )

    query = params.to_query_params()
    query.pop("api_version", None)

    response = build_and_execute(
        ENDPOINT_CP_DOWNLOAD, query, server=server, api_version=api_version
    )
    return parse_response(response, simplify=simplify, dataframe_type=dataframe_type)


def get_cp_ki(
    country: str,
    povline: float | None = 2.15,
    version: str | None = None,
    ppp_version: int = 2017,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Get country profile key indicators.

    Mirrors ``pipr::get_cp_ki()``. When *simplify* is ``True``,
    calls :func:`unnest_ki` to flatten the nested response.

    Args:
        country: Single ISO3 country code (required).
        povline: Poverty line in 2017 PPP USD per day (default 2.15).
            When ``ppp_version=2011`` and *povline* is ``None``,
            defaults to 1.9.
        version: Data version string.
        ppp_version: PPP base year (default 2017).
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        simplify: If ``True`` (default), return a flat DataFrame via
            :func:`unnest_ki`.
        server: Server target.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        A flat DataFrame of key indicators when *simplify* is ``True``, or a
        :class:`~povineq._response.PIPResponse` when *simplify* is ``False``.

    Raises:
        PIPValidationError: If *country* is missing or is a list.

    Example:
        >>> import povineq
        >>> df = povineq.get_cp_ki(country="IDN")
    """
    logger.debug("get_cp_ki", country=country, povline=povline)

    params = CpKiParams(
        country=country,
        povline=povline,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        api_version=api_version,
    )

    query = params.to_query_params()
    query.pop("api_version", None)

    response = build_and_execute(
        ENDPOINT_CP_KEY_INDICATORS, query, server=server, api_version=api_version
    )

    # cp-key-indicators returns JSON only.  Parse the response body once and
    # branch: unnest_ki (simplify=True) operates on the raw dict directly;
    # parse_response (simplify=False) wraps it in a PIPResponse.
    if simplify:
        raw = json.loads(response.text)
        return unnest_ki(raw)

    return parse_response(response, simplify=False, dataframe_type=dataframe_type)


def unnest_ki(raw: dict | list) -> pd.DataFrame:
    """Flatten nested key-indicator response into a single DataFrame.

    Mirrors ``pipr::unnest_ki()``. Extracts headcount, population, GNI,
    GDP growth, MPM headcount, and shared prosperity tables from the nested
    JSON structure and merges them on ``(country_code, reporting_year)``.

    Args:
        raw: Parsed JSON from the ``cp-key-indicators`` endpoint — either a
            dict (single country) or a list containing one dict.

    Returns:
        A flat :class:`~pandas.DataFrame` with one row per
        ``(country_code, reporting_year)`` combination.

    Example:
        >>> import povineq
        >>> df = povineq.get_cp_ki(country="IDN")  # calls unnest_ki internally
    """
    if isinstance(raw, list):
        raw = raw[0] if raw else {}

    if not raw:
        logger.warning("unnest_ki: received an empty response. Returning an empty DataFrame.")
        return pd.DataFrame()

    def _extract(key: str) -> pd.DataFrame:
        val = raw.get(key)
        if val is None:
            return pd.DataFrame()
        if isinstance(val, list) and len(val) == 1 and not isinstance(val[0], dict):
            # Wrapped list-of-lists
            inner = val[0]
            if isinstance(inner, list):
                return pd.DataFrame(inner) if inner else pd.DataFrame()
        if isinstance(val, list):
            # Could be list-of-dicts directly or list containing a list-of-dicts
            if val and isinstance(val[0], dict):
                return pd.DataFrame(val)
            if val and isinstance(val[0], list):
                return pd.DataFrame(val[0]) if val[0] else pd.DataFrame()
        if isinstance(val, dict):
            return pd.DataFrame([val])
        return pd.DataFrame()

    headcount = _extract("headcount")
    headcount_national = _extract("headcount_national")
    mpm_headcount = _extract("mpm_headcount")
    pop = _extract("pop")
    gni = _extract("gni")
    gdp_growth = _extract("gdp_growth")
    shared_prosperity = _extract("shared_prosperity")

    # Deduplicate GNI and GDP growth on key columns (pipr behaviour)
    merge_cols = ["country_code", "reporting_year"]
    gni = gni.drop_duplicates(subset=merge_cols) if not gni.empty and all(c in gni.columns for c in merge_cols) else gni
    gdp_growth = gdp_growth.drop_duplicates(subset=merge_cols) if not gdp_growth.empty and all(c in gdp_growth.columns for c in merge_cols) else gdp_growth

    # Merge all on (country_code, reporting_year) with full outer joins
    # Merge all sub-tables on (country_code, reporting_year) using outer joins.
    # Start with an empty accumulator; grow it left-to-right so later tables
    # extend rather than overwrite columns from earlier ones.
    dfs = [headcount, headcount_national, mpm_headcount, pop, gni, gdp_growth]
    result = pd.DataFrame()
    for df_part in dfs:
        if df_part.empty:
            continue
        if result.empty:
            result = df_part
        else:
            common = [c for c in merge_cols if c in result.columns and c in df_part.columns]
            if common:
                # Standard case: join on shared key columns.
                result = result.merge(df_part, on=common, how="outer")
            else:
                # No common key columns — a cross join would create a Cartesian
                # product of all rows, silently inflating the output.  Warn the
                # caller so the issue is visible in logs.
                logger.warning(
                    "unnest_ki: no common merge keys found when joining "
                    f"a sub-table with columns {list(df_part.columns)}. "
                    "Performing a cross join, which may produce spurious rows."
                )
                result = result.merge(df_part, how="cross")

    # Append shared_prosperity (merges only on country_code)
    if not shared_prosperity.empty and not result.empty:
        cc_col = "country_code"
        if cc_col in result.columns and cc_col in shared_prosperity.columns:
            result = result.merge(shared_prosperity, on=cc_col, how="outer")

    return result
