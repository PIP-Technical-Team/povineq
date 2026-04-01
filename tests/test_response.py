"""Tests for response parsing (_response.py) using fixture bytes."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from povineq._errors import PIPError
from povineq._response import PIPResponse, _parse_arrow, _parse_csv, _parse_json, parse_response


def _make_mock_response(content: bytes, content_type: str, status: int = 200) -> MagicMock:
    """Build a minimal mock httpx.Response."""
    resp = MagicMock()
    resp.content = content
    resp.text = content.decode("utf-8", errors="replace")
    resp.headers = {"content-type": content_type}
    resp.status_code = status
    resp.url = "https://api.worldbank.org/pip/v1/pip"
    resp.reason_phrase = "OK"
    return resp


def _make_arrow_bytes(records: list[dict]) -> bytes:
    table = pa.Table.from_pydict({k: [r[k] for r in records] for k in records[0]})
    buf = io.BytesIO()
    writer = ipc.new_file(buf, table.schema)
    writer.write_table(table)
    writer.close()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Format-specific parsers
# ---------------------------------------------------------------------------

class TestParseArrow:
    def test_basic(self):
        bs = _make_arrow_bytes([{"a": 1, "b": "x"}])
        table = _parse_arrow(bs)
        assert isinstance(table, pa.Table)
        assert table.schema.names == ["a", "b"]
        assert table.column("a")[0].as_py() == 1

    def test_multiple_rows(self):
        bs = _make_arrow_bytes([{"x": i} for i in range(5)])
        table = _parse_arrow(bs)
        assert len(table) == 5


class TestParseJson:
    def test_list_of_dicts(self):
        data = [{"a": 1}, {"a": 2}]
        df = _parse_json(json.dumps(data))
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_dict_returns_dataframe(self):
        data = {"tables": ["cpi", "gdp"]}
        result = _parse_json(json.dumps(data))
        assert isinstance(result, pd.DataFrame)

    def test_is_raw_returns_dict(self):
        data = {"status": "ok"}
        result = _parse_json(json.dumps(data), is_raw=True)
        assert isinstance(result, dict)
        assert result["status"] == "ok"

    def test_is_raw_returns_list(self):
        data = [1, 2, 3]
        result = _parse_json(json.dumps(data), is_raw=True)
        assert result == [1, 2, 3]


class TestParseCsv:
    def test_basic(self):
        csv = "a,b\n1,x\n2,y\n"
        df = _parse_csv(csv)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["a", "b"]
        assert len(df) == 2


# ---------------------------------------------------------------------------
# parse_response integration
# ---------------------------------------------------------------------------

class TestParseResponseArrow:
    def test_simplify_true_returns_dataframe(self, stats_arrow_bytes):
        resp = _make_mock_response(stats_arrow_bytes, "application/vnd.apache.arrow.file")
        result = parse_response(resp, simplify=True)
        assert isinstance(result, pd.DataFrame)

    def test_simplify_false_returns_pip_response(self, stats_arrow_bytes):
        resp = _make_mock_response(stats_arrow_bytes, "application/vnd.apache.arrow.file")
        result = parse_response(resp, simplify=False)
        assert isinstance(result, PIPResponse)
        assert isinstance(result.content, pd.DataFrame)
        assert result.status == 200

    def test_column_rename_applied(self):
        # reporting_year → year, reporting_pop → pop
        bs = _make_arrow_bytes([{
            "country_code": "AGO",
            "reporting_year": 2000,
            "reporting_pop": 1000000.0,
        }])
        resp = _make_mock_response(bs, "application/vnd.apache.arrow.file")
        df = parse_response(resp, simplify=True)
        assert "year" in df.columns
        assert "pop" in df.columns
        assert "reporting_year" not in df.columns
        assert "reporting_pop" not in df.columns


class TestParseResponseJson:
    def test_simplify_true_returns_dataframe(self, stats_json_bytes):
        resp = _make_mock_response(stats_json_bytes, "application/json")
        result = parse_response(resp, simplify=True)
        assert isinstance(result, pd.DataFrame)

    def test_simplify_false_returns_pip_response(self, stats_json_bytes):
        resp = _make_mock_response(stats_json_bytes, "application/json")
        result = parse_response(resp, simplify=False)
        assert isinstance(result, PIPResponse)


class TestParseResponseCsv:
    def test_simplify_true_returns_dataframe(self, stats_csv_bytes):
        resp = _make_mock_response(stats_csv_bytes, "text/csv")
        result = parse_response(resp, simplify=True)
        assert isinstance(result, pd.DataFrame)
        assert "country_code" in result.columns

    def test_simplify_false_returns_pip_response(self, stats_csv_bytes):
        resp = _make_mock_response(stats_csv_bytes, "text/csv")
        result = parse_response(resp, simplify=False)
        assert isinstance(result, PIPResponse)


class TestParseResponseUnsupported:
    def test_unknown_content_type_raises(self):
        resp = _make_mock_response(b"<html/>", "text/html")
        with pytest.raises(PIPError, match="Unsupported"):
            parse_response(resp, simplify=True)


class TestDecilePivoting:
    def test_deciles_pivoted_in_json(self):
        data = [{"country": "AGO", "deciles": [0.1, 0.2, 0.3]}]
        bs = json.dumps(data).encode()
        resp = _make_mock_response(bs, "application/json")
        df = parse_response(resp, simplify=True)
        assert "decile1" in df.columns
        assert "decile2" in df.columns
        assert "decile3" in df.columns
        assert "deciles" not in df.columns
        assert df["decile1"].iloc[0] == pytest.approx(0.1)

    def test_no_deciles_unchanged(self):
        data = [{"country": "AGO", "value": 42}]
        bs = json.dumps(data).encode()
        resp = _make_mock_response(bs, "application/json")
        df = parse_response(resp, simplify=True)
        assert "country" in df.columns


class TestPolarsSwitching:
    def test_pandas_default(self, stats_json_bytes):
        resp = _make_mock_response(stats_json_bytes, "application/json")
        result = parse_response(resp, simplify=True, dataframe_type="pandas")
        assert isinstance(result, pd.DataFrame)

    def test_polars_raises_if_not_installed(self, stats_json_bytes, monkeypatch):
        import sys
        # Mask polars
        monkeypatch.setitem(sys.modules, "polars", None)
        resp = _make_mock_response(stats_json_bytes, "application/json")
        with pytest.raises((ImportError, TypeError)):
            parse_response(resp, simplify=True, dataframe_type="polars")


class TestToTargetType:
    """Direct tests for _to_target_type() helper."""

    def test_arrow_table_to_pandas(self):
        from povineq._response import _to_target_type

        table = pa.table({"a": [1, 2], "b": ["x", "y"]})
        result = _to_target_type(table, "pandas")
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["a", "b"]

    def test_pandas_to_pandas_passthrough(self):
        from povineq._response import _to_target_type

        df = pd.DataFrame({"a": [1]})
        result = _to_target_type(df, "pandas")
        assert isinstance(result, pd.DataFrame)


class TestApplyPostProcessing:
    """Direct tests for _apply_post_processing() helper."""

    def test_renames_columns(self):
        from povineq._response import _apply_post_processing

        df = pd.DataFrame({"reporting_year": [2000], "country_code": ["AGO"]})
        result = _apply_post_processing(df)
        assert "year" in result.columns
        assert "reporting_year" not in result.columns

    def test_pivots_deciles(self):
        from povineq._response import _apply_post_processing

        df = pd.DataFrame({"country_code": ["AGO"], "deciles": [[0.1, 0.2]]})
        result = _apply_post_processing(df)
        assert "decile1" in result.columns
        assert "deciles" not in result.columns


class TestEmptyResponses:
    """Edge cases: empty Arrow, JSON, and CSV responses."""

    def test_empty_json_array(self):
        resp = _make_mock_response(b"[]", "application/json")
        df = parse_response(resp, simplify=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_empty_csv_header_only(self):
        resp = _make_mock_response(b"country_code,year\n", "text/csv")
        df = parse_response(resp, simplify=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "country_code" in df.columns

    def test_empty_arrow(self):
        # Build a valid Arrow IPC file with 0 rows.
        schema = pa.schema([("country_code", pa.string()), ("year", pa.int32())])
        table = pa.table({"country_code": pa.array([], type=pa.string()), "year": pa.array([], type=pa.int32())})
        buf = io.BytesIO()
        writer = ipc.new_file(buf, schema)
        writer.write_table(table)
        writer.close()
        resp = _make_mock_response(buf.getvalue(), "application/vnd.apache.arrow.file")
        df = parse_response(resp, simplify=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
