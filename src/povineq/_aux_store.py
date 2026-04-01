"""In-memory auxiliary table store — equivalent to pipr's ``.pip`` environment."""

from __future__ import annotations

import pandas as pd

_store: dict[str, pd.DataFrame] = {}


def set_aux(table: str, value: pd.DataFrame, replace: bool = False) -> bool:
    """Store an auxiliary table in the in-memory store.

    Args:
        table: Name to store the table under.
        value: DataFrame to store.
        replace: If ``False`` (default) and the table already exists, raises
            a :exc:`ValueError`. If ``True``, silently overwrites.

    Returns:
        ``True`` if the table was stored successfully.

    Raises:
        ValueError: If *table* already exists and *replace* is ``False``.

    Example:
        >>> import pandas as pd
        >>> from povineq._aux_store import set_aux, call_aux
        >>> df = pd.DataFrame({"a": [1]})
        >>> set_aux("my_table", df)
        True
        >>> call_aux("my_table")
           a
        0  1
    """
    if table in _store and not replace:
        raise ValueError(
            f"Table {table!r} already exists in the store. "
            "Pass replace=True to overwrite."
        )
    _store[table] = value
    return True


def call_aux(table: str | None = None) -> pd.DataFrame | list[str]:
    """Retrieve a stored auxiliary table, or list all available tables.

    Args:
        table: Name of the table to retrieve. If ``None``, returns a list of
            all table names currently in the store.

    Returns:
        The stored :class:`~pandas.DataFrame` if *table* is specified, or a
        ``list[str]`` of table names if *table* is ``None``.

    Raises:
        KeyError: If the requested *table* does not exist in the store.

    Example:
        >>> call_aux()          # returns list of stored table names
        []
        >>> call_aux("missing") # raises KeyError
    """
    if table is None:
        return list(_store.keys())

    if table not in _store:
        raise KeyError(
            f"Table {table!r} not found in store. "
            "Use get_aux(table, assign_tb=True) to fetch and store it first."
        )
    return _store[table]
