"""Utility functions for povineq.

Provides data-frame helpers that mirror pipr's internal utilities,
most importantly :func:`change_grouped_stats_to_csv` for decile pivoting.
"""

from __future__ import annotations

import pandas as pd


def change_grouped_stats_to_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Expand a ``deciles`` list column into individual ``decile1``--``decileN`` columns.

    Mirrors ``pipr::change_grouped_stats_to_csv()``. When the PIP API returns
    grouped statistics in JSON or RDS format, the decile values are packed into
    a single ``"deciles"`` column whose cells contain lists. This function
    unpacks those lists into separate columns and drops the original list column.

    If the DataFrame has no ``"deciles"`` column, it is returned unchanged.

    Args:
        df: DataFrame potentially containing a ``"deciles"`` list-column.

    Returns:
        DataFrame with individual ``"decile1"``, ``"decile2"``, … columns
        replacing the ``"deciles"`` column.

    Example:
        >>> import pandas as pd
        >>> from povineq.utils import change_grouped_stats_to_csv
        >>> df = pd.DataFrame({"country": ["ALB"], "deciles": [[0.1, 0.2]]})
        >>> change_grouped_stats_to_csv(df)
          country  decile1  decile2
        0     ALB      0.1      0.2
    """
    if "deciles" not in df.columns:
        return df

    deciles_series = df["deciles"]

    # Determine the number of deciles from the first non-null row
    n_deciles = 0
    for val in deciles_series:
        if val is not None and hasattr(val, "__len__"):
            n_deciles = len(val)
            break

    if n_deciles == 0:
        return df.drop(columns=["deciles"])

    decile_cols = {f"decile{i + 1}": [] for i in range(n_deciles)}
    for val in deciles_series:
        if val is None or not hasattr(val, "__len__"):
            for i in range(n_deciles):
                decile_cols[f"decile{i + 1}"].append(None)
        else:
            for i in range(n_deciles):
                decile_cols[f"decile{i + 1}"].append(val[i] if i < len(val) else None)

    result = df.drop(columns=["deciles"]).copy()
    for col_name, values in decile_cols.items():
        result[col_name] = values

    return result


def rename_cols(df: pd.DataFrame, oldnames: list[str], newnames: list[str]) -> pd.DataFrame:
    """Rename DataFrame columns where old names exist, leaving others unchanged.

    Args:
        df: Input DataFrame.
        oldnames: Current column names to look for.
        newnames: Replacement names corresponding to each entry in *oldnames*.

    Returns:
        DataFrame with matching columns renamed.

    Raises:
        ValueError: If *oldnames* and *newnames* have different lengths.
    """
    if len(oldnames) != len(newnames):
        raise ValueError("oldnames and newnames must have the same length")

    rename_map = {
        old: new
        for old, new in zip(oldnames, newnames, strict=False)
        if old in df.columns
    }
    return df.rename(columns=rename_map)
