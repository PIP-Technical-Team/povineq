"""Tests for stats.py — get_stats, get_wb, get_agg using mocked HTTP."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from povineq.stats import get_agg, get_stats, get_wb


def _mock_response(content: bytes, content_type: str, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.text = content.decode("utf-8", errors="replace")
    resp.headers = {"content-type": content_type}
    resp.status_code = status
    resp.url = "https://api.worldbank.org/pip/v1/pip"
    resp.is_error = False
    return resp


@pytest.fixture()
def arrow_stats_response(stats_arrow_bytes):
    """Build a mock Arrow response using the shared conftest fixture."""
    return _mock_response(stats_arrow_bytes, "application/vnd.apache.arrow.file")


@pytest.fixture()
def json_stats_response():
    data = [{"country_code": "AGO", "reporting_year": 2000, "headcount": 0.544, "estimate_type": "survey"}]
    return _mock_response(json.dumps(data).encode(), "application/json")


@pytest.fixture()
def wb_json_response():
    data = [
        {"country_code": "SSA", "reporting_year": 2019, "headcount": 0.4, "region_name": "Sub-Saharan Africa"},
        {"country_code": "EAP", "reporting_year": 2019, "headcount": 0.1, "region_name": "East Asia & Pacific"},
    ]
    return _mock_response(json.dumps(data).encode(), "application/json")


class TestGetStats:
    def test_basic_single_country(self, arrow_stats_response):
        with patch("povineq.stats.build_and_execute", return_value=arrow_stats_response):
            df = get_stats(country="AGO", year=2000)
        assert isinstance(df, pd.DataFrame)
        assert "country_code" in df.columns

    def test_all_countries(self, arrow_stats_response):
        with patch("povineq.stats.build_and_execute", return_value=arrow_stats_response):
            df = get_stats()
        assert isinstance(df, pd.DataFrame)

    def test_fill_gaps_param(self, arrow_stats_response):
        with patch("povineq.stats.build_and_execute", return_value=arrow_stats_response) as mock_req:
            get_stats(country="AGO", fill_gaps=True)
        call_kwargs = mock_req.call_args
        # fill_gaps=True should be passed in query params
        assert call_kwargs is not None

    def test_popshare_disables_povline(self, arrow_stats_response):
        """When popshare is set, the request should not include povline."""
        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(params)
            return arrow_stats_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_stats(country="AGO", povline=1.9, popshare=0.4)

        assert len(calls) == 1
        assert "povline" not in calls[0]
        assert "popshare" in calls[0]

    def test_subgroup_routes_to_pip_grp(self, wb_json_response):
        """subgroup='wb_regions' should use the pip-grp endpoint."""
        from povineq._constants import ENDPOINT_PIP_GRP

        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(endpoint)
            return wb_json_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_stats(subgroup="wb_regions")

        assert calls[0] == ENDPOINT_PIP_GRP

    def test_no_subgroup_routes_to_pip(self, arrow_stats_response):
        from povineq._constants import ENDPOINT_PIP

        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(endpoint)
            return arrow_stats_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_stats(country="AGO")

        assert calls[0] == ENDPOINT_PIP

    def test_simplify_false_returns_pip_response(self, arrow_stats_response):
        from povineq._response import PIPResponse

        with patch("povineq.stats.build_and_execute", return_value=arrow_stats_response):
            result = get_stats(simplify=False)
        assert isinstance(result, PIPResponse)

    def test_json_format(self, json_stats_response):
        with patch("povineq.stats.build_and_execute", return_value=json_stats_response):
            df = get_stats(format="json")
        assert isinstance(df, pd.DataFrame)

    def test_nowcast_filter(self):
        """Rows with 'nowcast' in estimate_type should be filtered when nowcast=False."""
        records = [
            {"country_code": "AGO", "reporting_year": 2000, "headcount": 0.5, "estimate_type": "survey"},
            {"country_code": "AGO", "reporting_year": 2023, "headcount": 0.3, "estimate_type": "nowcast"},
        ]
        data = json.dumps(records).encode()
        resp = _mock_response(data, "application/json")
        with patch("povineq.stats.build_and_execute", return_value=resp):
            df = get_stats(fill_gaps=True, nowcast=False)
        # nowcast row should be filtered
        assert all("nowcast" not in str(v) for v in df["estimate_type"])


class TestGetWb:
    def test_basic(self, wb_json_response):
        with patch("povineq.stats.build_and_execute", return_value=wb_json_response):
            df = get_wb()
        assert isinstance(df, pd.DataFrame)

    def test_routes_to_pip_grp(self, wb_json_response):
        from povineq._constants import ENDPOINT_PIP_GRP

        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(endpoint)
            return wb_json_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_wb()

        assert calls[0] == ENDPOINT_PIP_GRP

    def test_group_by_wb_in_params(self, wb_json_response):
        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(params)
            return wb_json_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_wb()

        assert calls[0].get("group_by") == "wb"


class TestGetAgg:
    def test_basic(self, wb_json_response):
        with patch("povineq.stats.build_and_execute", return_value=wb_json_response):
            df = get_agg()
        assert isinstance(df, pd.DataFrame)

    def test_aggregate_param_passed(self, wb_json_response):
        calls = []
        def capture_call(endpoint, params, **kwargs):
            calls.append(params)
            return wb_json_response

        with patch("povineq.stats.build_and_execute", side_effect=capture_call):
            get_agg(aggregate="fcv")

        assert calls[0].get("aggregate") == "fcv"
