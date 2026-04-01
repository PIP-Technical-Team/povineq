"""Tests for auxiliary.py — get_aux, display_aux, call_aux, wrappers."""

from __future__ import annotations

import json
from unittest.mock import patch

import pandas as pd
import pytest

from povineq._aux_store import _store
from povineq.auxiliary import (
    call_aux,
    display_aux,
    get_aux,
    get_cpi,
    get_countries,
    get_gdp,
    get_ppp,
    get_regions,
    get_survey_means,
)


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


def _mock_resp(data: dict | list, status: int = 200):
    from unittest.mock import MagicMock
    resp = MagicMock()
    resp.content = json.dumps(data).encode()
    resp.text = json.dumps(data)
    resp.headers = {"content-type": "application/json"}
    resp.status_code = status
    resp.url = "https://api.worldbank.org/pip/v1/aux"
    resp.is_error = False
    return resp


class TestGetAuxNoTable:
    def test_no_table_returns_list(self, aux_json_bytes):
        resp = _mock_resp({"tables": ["countries", "gdp", "cpi"]})
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            result = get_aux()
        assert isinstance(result, list)
        assert "countries" in result
        assert "gdp" in result

    def test_no_table_simplify_false(self, aux_json_bytes):
        from povineq._response import PIPResponse
        resp = _mock_resp({"tables": ["countries"]})
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            result = get_aux(simplify=False)
        assert isinstance(result, PIPResponse)


class TestGetAuxWithTable:
    def test_gdp_table(self):
        data = [{"country_code": "AGO", "year": 2000, "gdp": 3000.0}]
        resp = _mock_resp(data)
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            df = get_aux("gdp")
        assert isinstance(df, pd.DataFrame)
        assert "country_code" in df.columns

    def test_assign_tb_true_stores_in_memory(self):
        data = [{"country_code": "AGO", "gdp": 3000.0}]
        resp = _mock_resp(data)
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            result = get_aux("gdp", assign_tb=True)
        assert result is True
        assert "gdp" in _store

    def test_assign_tb_str_stores_under_name(self):
        data = [{"country_code": "AGO", "gdp": 3000.0}]
        resp = _mock_resp(data)
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            get_aux("gdp", assign_tb="my_gdp")
        assert "my_gdp" in _store

    def test_assign_tb_invalid_raises(self):
        data = [{"a": 1}]
        resp = _mock_resp(data)
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            with pytest.raises(ValueError, match="assign_tb"):
                get_aux("gdp", assign_tb=42)  # not bool or str


class TestDisplayAux:
    def test_returns_list_of_tables(self):
        tables = ["countries", "gdp", "cpi"]
        resp = _mock_resp({"tables": tables})
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            result = display_aux()
        assert isinstance(result, list)
        assert "countries" in result
        assert "gdp" in result


class TestCallAux:
    def test_empty_store_returns_empty_list(self):
        result = call_aux()
        assert result == []

    def test_missing_table_raises(self):
        with pytest.raises(KeyError):
            call_aux("nonexistent")

    def test_retrieve_after_assign(self):
        data = [{"country_code": "AGO"}]
        resp = _mock_resp(data)
        with patch("povineq.auxiliary.build_and_execute", return_value=resp):
            get_aux("countries", assign_tb=True)
        retrieved = call_aux("countries")
        assert isinstance(retrieved, pd.DataFrame)


class TestConvenienceWrappers:
    """Each wrapper should call get_aux with the correct table name."""

    def _setup_mock(self, table_name: str):
        data = [{"table": table_name, "value": 1}]
        return _mock_resp(data)

    @pytest.mark.parametrize("fn,table", [
        (get_countries, "countries"),
        (get_regions, "regions"),
        (get_cpi, "cpi"),
        (get_gdp, "gdp"),
        (get_ppp, "ppp"),
        (get_survey_means, "survey_means"),
    ])
    def test_wrapper_uses_correct_table(self, fn, table):
        calls = []
        def capture(endpoint, params, **kwargs):
            calls.append(params.get("table"))
            return self._setup_mock(table)

        with patch("povineq.auxiliary.build_and_execute", side_effect=capture):
            fn()

        assert calls[0] == table
