"""Auxiliary data functions and convenience wrappers."""

from __future__ import annotations

from typing import Callable, Literal

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

        if not isinstance(rt, pd.DataFrame):
            logger.warning(
                "assign_tb requires simplify=True to store the table in memory; "
                "got a PIPResponse object. The table was NOT stored."
            )
        elif isinstance(rt, pd.DataFrame):
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
        logger.info("Available auxiliary tables:")
        for t in result:
            logger.info(f"  - {t}")
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


def _make_aux_getter(table_name: str, table_description: str) -> "Callable":
    """Factory that generates a typed convenience wrapper around :func:`get_aux`.

    Each generated function fetches a single named auxiliary table and documents
    its parameters. Using a factory eliminates ~170 lines of boilerplate while
    keeping individual per-table functions with proper ``__name__`` and
    ``__doc__`` attributes for IDE autocompletion and ``help()``.

    Args:
        table_name: The auxiliary table name passed to ``get_aux(table=...)``.
        table_description: Short description inserted into the docstring.

    Returns:
        A callable with the same signature as :func:`get_aux` (minus *table*,
        *assign_tb*, and *replace*).
    """

    def _getter(
        version: str | None = None,
        ppp_version: int | None = None,
        release_version: str | None = None,
        api_version: str = API_VERSION,
        format: str = "json",
        simplify: bool = True,
        server: str | None = None,
        dataframe_type: Literal["pandas", "polars"] = "pandas",
    ) -> "pd.DataFrame | PIPResponse":
        return get_aux(
            table=table_name,
            version=version,
            ppp_version=ppp_version,
            release_version=release_version,
            api_version=api_version,
            format=format,
            simplify=simplify,
            server=server,
            dataframe_type=dataframe_type,
        )

    _getter.__name__ = f"get_{table_name}"
    _getter.__qualname__ = f"get_{table_name}"
    _getter.__doc__ = f"""Return the auxiliary ``{table_name}`` table.

    {table_description}

    Args:
        version: Data version string.
        ppp_version: PPP base year.
        release_version: Release date in ``YYYYMMDD`` format.
        api_version: API version.
        format: Response format — ``"json"`` (default) or ``"csv"``.
        simplify: Return a DataFrame when ``True`` (default).
        server: Server target.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        A :class:`~pandas.DataFrame` when *simplify* is ``True``, or a
        :class:`~povineq._response.PIPResponse` when *simplify* is ``False``.

    Example:
        >>> import povineq
        >>> df = povineq.get_{table_name}()
    """
    return _getter


# ---------------------------------------------------------------------------
# Per-table convenience getters — generated by _make_aux_getter
# ---------------------------------------------------------------------------

get_countries = _make_aux_getter(
    "countries",
    "Contains ISO3 country codes, country names, and World Bank region assignments.",
)
get_regions = _make_aux_getter(
    "regions",
    "Contains World Bank region codes and names.",
)
get_cpi = _make_aux_getter(
    "cpi",
    "Consumer Price Index data used to deflate welfare aggregates.",
)
get_dictionary = _make_aux_getter(
    "dictionary",
    "Data dictionary describing all variables returned by the PIP API.",
)
get_gdp = _make_aux_getter(
    "gdp",
    "GDP per capita series used in the PIP pipeline.",
)
get_incgrp_coverage = _make_aux_getter(
    "incgrp_coverage",
    "Survey coverage by income group.",
)
get_interpolated_means = _make_aux_getter(
    "interpolated_means",
    "Interpolated/extrapolated mean welfare values used for gap-filling.",
)
get_hfce = _make_aux_getter(
    "pce",
    "Household Final Consumption Expenditure (PCE/HFCE) series.",
)
get_pop = _make_aux_getter(
    "pop",
    "Population data by country and year.",
)
get_pop_region = _make_aux_getter(
    "pop_region",
    "Population data aggregated by World Bank region.",
)
get_ppp = _make_aux_getter(
    "ppp",
    "Purchasing Power Parity conversion factors.",
)
get_region_coverage = _make_aux_getter(
    "region_coverage",
    "Survey coverage by World Bank region.",
)
get_survey_means = _make_aux_getter(
    "survey_means",
    "Survey mean welfare values before interpolation.",
)
