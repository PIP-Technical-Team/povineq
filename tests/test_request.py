"""Tests for the _request module — error parsing and rate-limit extraction."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from povineq._errors import PIPAPIError, PIPConnectionError, PIPRateLimitError
from povineq._request import _extract_retry_after, _parse_api_error, build_and_execute


class TestExtractRetryAfter:
    def _make_resp(self, message: str) -> MagicMock:
        resp = MagicMock()
        resp.json.return_value = {"message": message}
        return resp

    def test_extracts_integer_seconds(self):
        resp = self._make_resp("Rate limit is exceeded. Try again in 30 seconds.")
        assert _extract_retry_after(resp) == 30.0

    def test_extracts_float_seconds(self):
        resp = self._make_resp("Rate limit is exceeded. Try again in 5.5 seconds.")
        assert _extract_retry_after(resp) == pytest.approx(5.5)

    def test_returns_zero_on_no_match(self):
        resp = self._make_resp("some other message")
        assert _extract_retry_after(resp) == 0.0

    def test_returns_zero_on_json_parse_error(self):
        resp = MagicMock()
        resp.json.side_effect = ValueError("bad json")
        assert _extract_retry_after(resp) == 0.0


class TestParseApiError:
    def _make_resp(self, status: int, body: dict | None = None) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status
        resp.reason_phrase = "Some Error"
        if body is not None:
            resp.json.return_value = body
        else:
            resp.json.side_effect = ValueError("no json")
        return resp

    def test_gateway_timeout_504(self):
        resp = self._make_resp(504)
        err = _parse_api_error(resp)
        assert isinstance(err, PIPAPIError)
        assert err.status_code == 504

    def test_bad_gateway_502(self):
        resp = self._make_resp(502)
        err = _parse_api_error(resp)
        assert err.status_code == 502

    def test_structured_pip_error(self):
        body = {
            "error": ["Invalid country code"],
            "details": {
                "country": {
                    "msg": ["Country XYZ not found"],
                    "valid": ["AGO", "ALB"],
                }
            },
        }
        resp = self._make_resp(400, body)
        err = _parse_api_error(resp)
        assert err.status_code == 400
        assert "Invalid country code" in err.error_message
        assert "Country XYZ not found" in err.details
        assert "AGO" in err.valid_values

    def test_falls_back_on_bad_json(self):
        resp = self._make_resp(500)
        err = _parse_api_error(resp)
        assert err.status_code == 500


class TestBuildAndExecuteConnectionError:
    """Verify that all transport-level errors are wrapped in PIPConnectionError."""

    def test_connect_error_raises_pip_connection_error(self, monkeypatch):
        def _raise_connect(*args, **kwargs):
            raise httpx.ConnectError("Connection refused")

        monkeypatch.setattr("povineq._request.get_client", lambda server: _make_mock_client(_raise_connect))
        with pytest.raises(PIPConnectionError, match="PIP API"):
            build_and_execute("pip", {})

    def test_timeout_error_raises_pip_connection_error(self, monkeypatch):
        def _raise_timeout(*args, **kwargs):
            raise httpx.TimeoutException("Timed out")

        monkeypatch.setattr("povineq._request.get_client", lambda server: _make_mock_client(_raise_timeout))
        with pytest.raises(PIPConnectionError, match="PIP API"):
            build_and_execute("pip", {})


def _make_mock_client(side_effect):
    """Return a minimal mock client whose .get() raises the given side_effect."""
    client = MagicMock()
    client.get.side_effect = side_effect
    return client
