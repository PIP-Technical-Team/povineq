"""Auxiliary data functions and convenience wrappers."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from loguru import logger

from povineq._aux_store import call_aux as _call_aux_store
from povineq._aux_store import set_aux
from povineq._constants import API_VERSION, ENDPOINT_AUX
from povineq._request import build_and_execute
from povineq._response import PIPResponse, parse_response
from povineq._validation import AuxParams


def get_aux(
    table: str | None = None,
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
    assign_tb: bool | str = False,
    replace: bool = False,
) -> pd.DataFrame | list[str] | PIPResponse | bool:
    """Fetch an auxiliary dataset from the PIP API.

    When no *table* is specified, returns a list of available table names.
    Mirrors ``pipr::get_aux()``.

    Args:
        table: Auxiliary table name (e.g. ``"gdp"``, ``"cpi"``). If ``None``,
            returns a list of available table names.
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        format: Response format — ``"json"`` (default) or ``"csv"``.
            Arrow is not supported for auxiliary tables.
        simplify: If ``True`` (default), return a DataFrame.
        server: Server target.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.
        assign_tb: If ``False`` (default), return data normally. If ``True``,
            store the table in memory under its own name. If a string, store
            it under that name.
        replace: If ``True``, overwrite existing in-memory tables.

    Returns:
        - A ``list[str]`` of table names when *table* is ``None``.
        - A :class:`~pandas.DataFrame` when *simplify* is ``True``.
        - A :class:`~povineq._response.PIPResponse` when *simplify* is ``False``.
        - ``True`` when *assign_tb* is set and the table was stored.

    Example:
        >>> import povineq
        >>> tables = povineq.get_aux()          # list of available tables
        >>> df = povineq.get_aux("gdp")         # fetch GDP table
        >>> povineq.get_aux("cpi", assign_tb=True)  # fetch and store in memory
    """
    params = AuxParams(
        table=table,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        api_version=api_version,
        format=format,
    )

    if table is None:
        # Return list of available tables
        query: dict[str, str] = {}
        if version is not None:
            query["version"] = version
        if release_version is not None:
            query["release_version"] = release_version

        response = build_and_execute(ENDPOINT_AUX, query, server=server, api_version=api_version)
        result = parse_response(response, simplify=simplify, dataframe_type=dataframe_type)

        if simplify and isinstance(result, pd.DataFrame) and "tables" in result.columns:
            # pd.json_normalize packs {"tables": [...]} into a single-row df;
            # the cell value is the list itself — unwrap it when needed.
            raw = result["tables"].iloc[0]
            tables_list: list[str] = raw if isinstance(raw, list) else result["tables"].tolist()
            logger.info(f"Available auxiliary tables: {tables_list}")
            return tables_list

        return result  # type: ignore[return-value]

    # Fetch specific table
    query = params.to_query_params()
    query.pop("api_version", None)

    response = build_and_execute(ENDPOINT_AUX, query, server=server, api_version=api_version)
    rt = parse_response(response, simplify=simplify, dataframe_type=dataframe_type)

    if assign_tb is not False:
        tb_name: str
        if assign_tb is True:
            tb_name = table
        elif isinstance(assign_tb, str):
            tb_name = assign_tb
        else:
            raise ValueError("assign_tb must be a bool or a string.")

        if isinstance(rt, pd.DataFrame):
            return set_aux(tb_name, rt, replace=replace)

    return rt  # type: ignore[return-value]


def display_aux(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
) -> pd.DataFrame | list[str]:
    """Display available auxiliary tables.

    Fetches the list of auxiliary tables and prints them. Mirrors
    ``pipr::display_aux()``.

    Args:
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        format: Response format.
        simplify: Passed to :func:`get_aux`.
        server: Server target.

    Returns:
        List of available table name strings.

    Example:
        >>> import povineq
        >>> povineq.display_aux()
    """
    result = get_aux(
        table=None,
        version=version,
        ppp_version=ppp_version,
        release_version=release_version,
        api_version=api_version,
        format=format,
        simplify=simplify,
        server=server,
    )

    if isinstance(result, list):
        print("Available auxiliary tables:")
        for t in result:
            print(f"  - {t}")
        return result

    return result  # type: ignore[return-value]


def call_aux(table: str | None = None) -> pd.DataFrame | list[str]:
    """Retrieve a previously stored auxiliary table from memory.

    Mirrors ``pipr::call_aux()``.

    Args:
        table: Table name to retrieve. If ``None``, lists all stored tables.

    Returns:
        The stored DataFrame, or a list of stored table names.

    Raises:
        KeyError: If the requested table is not in the store.

    Example:
        >>> import povineq
        >>> povineq.get_aux("gdp", assign_tb=True)
        >>> df = povineq.call_aux("gdp")
    """
    return _call_aux_store(table)


def get_countries(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``countries`` table.

    Args:
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        format: Response format.
        simplify: Return a DataFrame when ``True``.
        server: Server target.
        dataframe_type: ``"pandas"`` or ``"polars"``.

    Returns:
        DataFrame of countries with ISO codes and region assignments.

    Example:
        >>> import povineq
        >>> df = povineq.get_countries()
    """
    return get_aux(
        table="countries",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_regions(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``regions`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_regions()
    """
    return get_aux(
        table="regions",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_cpi(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``cpi`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_cpi()
    """
    return get_aux(
        table="cpi",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_dictionary(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``dictionary`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_dictionary()
    """
    return get_aux(
        table="dictionary",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_gdp(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``gdp`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_gdp()
    """
    return get_aux(
        table="gdp",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_incgrp_coverage(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``incgrp_coverage`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_incgrp_coverage()
    """
    return get_aux(
        table="incgrp_coverage",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_interpolated_means(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``interpolated_means`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_interpolated_means()
    """
    return get_aux(
        table="interpolated_means",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_hfce(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``pce`` (household final consumption expenditure) table.

    Example:
        >>> import povineq
        >>> df = povineq.get_hfce()
    """
    return get_aux(
        table="pce",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_pop(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``pop`` (population) table.

    Example:
        >>> import povineq
        >>> df = povineq.get_pop()
    """
    return get_aux(
        table="pop",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_pop_region(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``pop_region`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_pop_region()
    """
    return get_aux(
        table="pop_region",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_ppp(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``ppp`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_ppp()
    """
    return get_aux(
        table="ppp",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_region_coverage(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``region_coverage`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_region_coverage()
    """
    return get_aux(
        table="region_coverage",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )


def get_survey_means(
    version: str | None = None,
    ppp_version: int | None = None,
    release_version: str | None = None,
    api_version: str = API_VERSION,
    format: str = "json",
    simplify: bool = True,
    server: str | None = None,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
) -> pd.DataFrame | PIPResponse:
    """Return the auxiliary ``survey_means`` table.

    Example:
        >>> import povineq
        >>> df = povineq.get_survey_means()
    """
    return get_aux(
        table="survey_means",
        version=version, ppp_version=ppp_version, release_version=release_version,
        api_version=api_version, format=format, simplify=simplify,
        server=server, dataframe_type=dataframe_type,
    )
