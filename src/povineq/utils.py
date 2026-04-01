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

    # Only list/tuple cells are valid decile containers; strings would silently
    # corrupt output (each character would become a "decile value").
    valid_mask = deciles_series.map(lambda v: isinstance(v, (list, tuple)))
    valid_lengths = deciles_series[valid_mask].map(len)

    if valid_lengths.empty:
        return df.drop(columns=["deciles"])

    # Guard against rows with different decile counts — that would produce
    # ragged output with silent None-padding.
    if valid_lengths.nunique() != 1:
        raise ValueError(
            "Rows in the 'deciles' column have different list lengths "
            f"({sorted(valid_lengths.unique().tolist())}). Cannot pivot to columns."
        )

    n_deciles = int(valid_lengths.iloc[0])

    # Vectorised unpacking via map() — avoids Python-level apply loop.
    decile_data = pd.DataFrame(
        deciles_series.where(valid_mask).map(
            lambda v: list(v) if isinstance(v, (list, tuple)) else [None] * n_deciles
        ).tolist(),
        index=df.index,
    ).rename(columns=lambda i: f"decile{i + 1}")

    result = df.drop(columns=["deciles"])
    return pd.concat([result, decile_data], axis=1)


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
