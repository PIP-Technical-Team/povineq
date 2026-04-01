"""Response parsing for PIP API responses (Arrow, JSON, CSV formats)."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from typing import Literal

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
from loguru import logger

from povineq._constants import COLUMN_RENAMES
from povineq._errors import PIPError
from povineq.utils import change_grouped_stats_to_csv, rename_cols


@dataclass
class PIPResponse:
    """Full API response object returned when ``simplify=False``.

    Equivalent to pipr's ``pip_api`` S3 class.

    Attributes:
        url: The request URL as a string.
        status: HTTP status code.
        content_type: Content-Type header value.
        content: Parsed data as a pandas (or polars) DataFrame.
        response: The underlying :class:`httpx.Response`.
    """

    url: str
    status: int
    content_type: str
    content: pd.DataFrame
    response: httpx.Response


def _parse_arrow(content: bytes) -> pa.Table:
    """Parse an Apache Arrow IPC (Feather v2) response body.

    Returns the raw :class:`~pyarrow.Table` so the caller can choose between
    zero-copy conversion to polars (``pl.from_arrow``) or a pandas conversion,
    avoiding a double pass through numpy when polars is the target type.

    Args:
        content: Raw bytes from the HTTP response.

    Returns:
        Parsed :class:`~pyarrow.Table`.
    """
    reader = ipc.open_file(io.BytesIO(content))
    return reader.read_all()


def _parse_json(text: str, is_raw: bool = False) -> pd.DataFrame | dict | list:
    """Parse a JSON response body.

    When *is_raw* is ``True`` (health-check, pip-info), the parsed object
    is returned as-is (dict or list). Otherwise the result is normalised
    to a :class:`~pandas.DataFrame`.

    Args:
        text: UTF-8 JSON text from the HTTP response.
        is_raw: If ``True``, skip DataFrame conversion.

    Returns:
        Parsed data as a DataFrame (or raw dict/list when *is_raw*).
    """
    data = json.loads(text)

    if is_raw:
        return data

    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        # Flat dict → single-row DataFrame; nested → json_normalize
        try:
            return pd.json_normalize(data)
        except (ValueError, AttributeError, TypeError):
            logger.warning("json_normalize failed; falling back to single-row DataFrame.")
            return pd.DataFrame([data])

    return pd.DataFrame([{"value": data}])


def _parse_csv(text: str) -> pd.DataFrame:
    """Parse a CSV response body.

    Args:
        text: UTF-8 CSV text from the HTTP response.

    Returns:
        Parsed :class:`~pandas.DataFrame`.
    """
    return pd.read_csv(io.StringIO(text))


def _apply_post_processing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply column renaming and decile pivoting.

    Args:
        df: Raw parsed DataFrame.

    Returns:
        Post-processed DataFrame.
    """
    df = change_grouped_stats_to_csv(df)
    df = rename_cols(df, list(COLUMN_RENAMES.keys()), list(COLUMN_RENAMES.values()))
    return df


def _to_target_type(
    data: pa.Table | pd.DataFrame,
    dataframe_type: Literal["pandas", "polars"],
) -> pd.DataFrame:
    """Convert data to the requested DataFrame type.

    Accepts either a :class:`~pyarrow.Table` (for zero-copy polars conversion)
    or a :class:`~pandas.DataFrame`. When *dataframe_type* is ``"polars"`` and
    the input is already an Arrow Table, ``pl.from_arrow()`` is used directly —
    no intermediate numpy pass required.

    Args:
        data: Input Arrow Table or pandas DataFrame.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.

    Returns:
        DataFrame in the requested format.

    Raises:
        ImportError: If polars is requested but not installed.
    """
    if dataframe_type == "polars":
        try:
            import polars as pl

            if isinstance(data, pa.Table):
                return pl.from_arrow(data)  # zero-copy path
            return pl.from_pandas(data)
        except ImportError as exc:
            raise ImportError(
                "polars is not installed. Run: pip install povineq[polars]"
            ) from exc
    if isinstance(data, pa.Table):
        return data.to_pandas()
    return data


def parse_response(
    response: httpx.Response,
    simplify: bool = True,
    dataframe_type: Literal["pandas", "polars"] = "pandas",
    is_raw: bool = False,
) -> pd.DataFrame | PIPResponse | dict | list:
    """Parse an HTTP response from the PIP API.

    Dispatches to the appropriate format parser based on the
    ``Content-Type`` response header.

    Args:
        response: Completed :class:`httpx.Response`.
        simplify: If ``True`` (default), return a DataFrame directly.
            If ``False``, return a :class:`PIPResponse` wrapper.
        dataframe_type: ``"pandas"`` (default) or ``"polars"``.
        is_raw: If ``True``, skip DataFrame conversion (for health-check,
            pip-info endpoints that return plain dicts/lists).

    Returns:
        A DataFrame when *simplify* is ``True`` and *is_raw* is ``False``.
        A :class:`PIPResponse` when *simplify* is ``False``.
        A dict or list when *is_raw* is ``True``.

    Raises:
        PIPError: If the response Content-Type is not supported.
    """
    content_type = response.headers.get("content-type", "")

    if "application/vnd.apache.arrow.file" in content_type:
        table: pa.Table = _parse_arrow(response.content)
        # Arrow responses do not need decile pivoting (see pipr comment).
        # Rename columns directly on the Arrow Table (zero-copy) before
        # converting to the target type, avoiding a double numpy pass.
        if simplify and not is_raw:
            renamed_names = [COLUMN_RENAMES.get(name, name) for name in table.schema.names]
            table = table.rename_columns(renamed_names)
            return _to_target_type(table, dataframe_type)
        parsed: pd.DataFrame | dict | list = table.to_pandas()
        if isinstance(parsed, pd.DataFrame):
            parsed = rename_cols(
                parsed, list(COLUMN_RENAMES.keys()), list(COLUMN_RENAMES.values())
            )

    elif "application/json" in content_type:
        parsed = _parse_json(response.text, is_raw=is_raw)
        if is_raw:
            return parsed
        if simplify and isinstance(parsed, pd.DataFrame):
            parsed = _apply_post_processing(parsed)
            return _to_target_type(parsed, dataframe_type)

    elif "text/csv" in content_type:
        parsed = _parse_csv(response.text)
        if simplify and isinstance(parsed, pd.DataFrame):
            parsed = _apply_post_processing(parsed)
            return _to_target_type(parsed, dataframe_type)

    else:
        raise PIPError(f"Unsupported Content-Type: {content_type!r}")

    # simplify=False path
    if isinstance(parsed, pd.DataFrame):
        parsed = _apply_post_processing(parsed)
        parsed = _to_target_type(parsed, dataframe_type)

    return PIPResponse(
        url=str(response.url),
        status=response.status_code,
        content_type=content_type,
        content=parsed,  # type: ignore[arg-type]
        response=response,
    )
