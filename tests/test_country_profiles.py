"""Tests for country_profiles.py — get_cp, get_cp_ki, unnest_ki."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pytest

from povineq.country_profiles import get_cp, get_cp_ki, unnest_ki


def _make_arrow_bytes(records: list[dict]) -> bytes:
    table = pa.Table.from_pydict({k: [r[k] for r in records] for k in records[0]})
    buf = io.BytesIO()
    writer = ipc.new_file(buf, table.schema)
    writer.write_table(table)
    writer.close()
    return buf.getvalue()


def _mock_resp(content: bytes, content_type: str, url: str = "https://api.worldbank.org/pip/v1/cp-download") -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.text = content.decode("utf-8", errors="replace")
    resp.headers = {"content-type": content_type}
    resp.status_code = 200
    resp.url = url
    resp.is_error = False
    return resp


@pytest.fixture()
def cp_arrow_response():
    records = [{"country_code": "AGO", "reporting_year": 2000, "poverty_line": 2.15, "headcount": 0.5}]
    return _mock_resp(_make_arrow_bytes(records), "application/vnd.apache.arrow.file")


class TestGetCp:
    def test_basic(self, cp_arrow_response):
        with patch("povineq.country_profiles.build_and_execute", return_value=cp_arrow_response):
            df = get_cp(country="AGO")
        assert isinstance(df, pd.DataFrame)

    def test_default_params(self, cp_arrow_response):
        """Default ppp_version=2017, povline=2.15."""
        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(params)
            return cp_arrow_response

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp()

        q = calls[0]
        assert q.get("ppp_version") == "2017"
        assert q.get("povline") == "2.15"

    def test_ppp_version_2011_no_povline_uses_1_9(self, cp_arrow_response):
        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(params)
            return cp_arrow_response

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp(ppp_version=2011, povline=None)

        q = calls[0]
        assert q.get("povline") == "1.9"

    def test_explicit_povline_not_overridden(self, cp_arrow_response):
        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(params)
            return cp_arrow_response

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp(ppp_version=2011, povline=3.65)

        q = calls[0]
        assert q.get("povline") == "3.65"

    def test_routes_to_cp_download(self, cp_arrow_response):
        from povineq._constants import ENDPOINT_CP_DOWNLOAD

        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(endpoint)
            return cp_arrow_response

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp()

        assert calls[0] == ENDPOINT_CP_DOWNLOAD

    def test_simplify_false_returns_pip_response(self, cp_arrow_response):
        from povineq._response import PIPResponse

        with patch("povineq.country_profiles.build_and_execute", return_value=cp_arrow_response):
            result = get_cp(simplify=False)
        assert isinstance(result, PIPResponse)


class TestGetCpKi:
    def test_country_required(self):
        from pydantic import ValidationError
        with pytest.raises((ValidationError, TypeError, ValueError)):
            get_cp_ki(country=None)

    def test_routes_to_cp_key_indicators(self):
        from povineq._constants import ENDPOINT_CP_KEY_INDICATORS

        ki_data = {
            "headcount": [{"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1}],
            "headcount_national": [],
            "mpm_headcount": [],
            "pop": [],
            "gni": [],
            "gdp_growth": [],
            "shared_prosperity": [],
        }
        resp = _mock_resp(
            json.dumps(ki_data).encode(),
            "application/json",
            url="https://api.worldbank.org/pip/v1/cp-key-indicators"
        )

        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(endpoint)
            return resp

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp_ki(country="IDN")

        assert calls[0] == ENDPOINT_CP_KEY_INDICATORS


class TestUnnestKi:
    def test_basic_unnest(self):
        raw = {
            "headcount": [{"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1}],
            "headcount_national": [{"country_code": "IDN", "reporting_year": 2019, "headcount_nat": 0.2}],
            "mpm_headcount": [],
            "pop": [{"country_code": "IDN", "reporting_year": 2019, "pop": 270e6}],
            "gni": [{"country_code": "IDN", "reporting_year": 2019, "gni": 4000.0}],
            "gdp_growth": [{"country_code": "IDN", "reporting_year": 2019, "gdp_growth": 5.0}],
            "shared_prosperity": [{"country_code": "IDN", "sp": 0.03}],
        }
        df = unnest_ki(raw)
        assert isinstance(df, pd.DataFrame)
        assert "country_code" in df.columns
        assert "reporting_year" in df.columns

    def test_empty_raw_returns_empty_df(self):
        df = unnest_ki({})
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_list_input(self):
        raw = [{"headcount": [{"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1}]}]
        df = unnest_ki(raw)
        assert isinstance(df, pd.DataFrame)


class TestGetCpWithCountryList:
    """P2.18 — get_cp() with a list of country codes."""

    @pytest.fixture()
    def cp_resp(self):
        records = [{"country_code": "AGO", "reporting_year": 2000, "headcount": 0.5}]
        table = pa.Table.from_pydict({k: [r[k] for r in records] for k in records[0]})
        buf = io.BytesIO()
        writer = ipc.new_file(buf, table.schema)
        writer.write_table(table)
        writer.close()
        resp = MagicMock()
        resp.content = buf.getvalue()
        resp.text = ""
        resp.headers = {"content-type": "application/vnd.apache.arrow.file"}
        resp.status_code = 200
        resp.url = "https://api.worldbank.org/pip/v1/cp-download"
        resp.is_error = False
        return resp

    def test_list_joined_as_comma_separated(self, cp_resp):
        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(params)
            return cp_resp

        with patch("povineq.country_profiles.build_and_execute", side_effect=capture):
            get_cp(country=["AGO", "ALB"])

        assert "," in calls[0].get("country", "")
        assert "AGO" in calls[0]["country"]
        assert "ALB" in calls[0]["country"]


class TestUnnestKiNestingPatterns:
    """P2.19 — unnest_ki handles multiple nesting structures."""

    def test_empty_list_input_returns_empty_df(self):
        df = unnest_ki([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_missing_keys_returns_partial_df(self):
        """Raw dict with only some keys present should not raise."""
        raw = {
            "headcount": [{"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1}],
        }
        df = unnest_ki(raw)
        assert isinstance(df, pd.DataFrame)
        assert "country_code" in df.columns

    def test_value_as_dict_wraps_to_single_row(self):
        """When a key's value is a plain dict, it should be wrapped to one row."""
        raw = {
            "headcount": {"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1},
        }
        df = unnest_ki(raw)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1

    def test_mixed_null_tables_handled(self):
        """Tables that are None should be treated as empty."""
        raw = {
            "headcount": [{"country_code": "IDN", "reporting_year": 2019, "headcount": 0.1}],
            "gni": None,
            "gdp_growth": None,
        }
        df = unnest_ki(raw)
        assert isinstance(df, pd.DataFrame)
        assert "country_code" in df.columns
