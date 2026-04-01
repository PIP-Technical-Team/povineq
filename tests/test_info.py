"""Tests for info.py — check_api, get_versions, get_pip_info."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pandas as pd

from povineq.info import check_api, get_pip_info, get_versions


def _mock_resp(data: dict | list, content_type: str = "application/json") -> MagicMock:
    resp = MagicMock()
    resp.content = json.dumps(data).encode()
    resp.text = json.dumps(data)
    resp.headers = {"content-type": content_type}
    resp.status_code = 200
    resp.url = "https://api.worldbank.org/pip/v1/health-check"
    resp.is_error = False
    return resp


class TestCheckApi:
    def test_returns_dict(self):
        health = {"status": "ok", "version": "v1"}
        resp = _mock_resp(health)
        with patch("povineq.info.build_and_execute", return_value=resp):
            result = check_api()
        assert isinstance(result, dict)

    def test_routes_to_health_check(self):
        from povineq._constants import ENDPOINT_HEALTH_CHECK

        calls = []
        def capture(endpoint, _params, **_kwargs):
            calls.append(endpoint)
            return _mock_resp({"status": "ok"})

        with patch("povineq.info.build_and_execute", side_effect=capture):
            check_api()

        assert calls[0] == ENDPOINT_HEALTH_CHECK


class TestGetVersions:
    def test_simplify_true_returns_df(self):
        versions = [{"version": "20240101", "ppp_year": 2017}]
        resp = _mock_resp(versions)
        resp.url = "https://api.worldbank.org/pip/v1/versions"
        with patch("povineq.info.build_and_execute", return_value=resp):
            result = get_versions()
        assert isinstance(result, pd.DataFrame)

    def test_routes_to_versions_endpoint(self):
        from povineq._constants import ENDPOINT_VERSIONS

        calls = []
        def capture(endpoint, _params, **_kwargs):
            calls.append(endpoint)
            return _mock_resp([{"version": "v1"}])

        with patch("povineq.info.build_and_execute", side_effect=capture):
            get_versions()

        assert calls[0] == ENDPOINT_VERSIONS


class TestGetPipInfo:
    def test_returns_dict(self):
        info = {"api_version": "v1", "endpoints": ["pip", "aux"]}
        resp = _mock_resp(info)
        resp.url = "https://api.worldbank.org/pip/v1/pip-info"
        with patch("povineq.info.build_and_execute", return_value=resp):
            result = get_pip_info()
        assert isinstance(result, dict)

    def test_routes_to_pip_info_endpoint(self):
        from povineq._constants import ENDPOINT_PIP_INFO

        calls = []
        def capture(endpoint, _params, **_kwargs):
            calls.append(endpoint)
            return _mock_resp({"info": True})

        with patch("povineq.info.build_and_execute", side_effect=capture):
            get_pip_info()

        assert calls[0] == ENDPOINT_PIP_INFO
