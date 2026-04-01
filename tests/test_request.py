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

    def test_details_as_list(self):
        """P2.13 — details can be a list of objects instead of a dict."""
        body = {
            "error": ["Validation error"],
            "details": [{"field": "country", "msg": ["Country not found"]}],
        }
        resp = self._make_resp(422, body)
        err = _parse_api_error(resp)
        assert err.status_code == 422
        assert "Validation error" in err.error_message

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


class TestBuildAndExecuteRetries:
    """P1.3 — verify 429 retry behaviour in build_and_execute()."""

    def _make_rate_limit_resp(self, wait: int = 1) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 429
        resp.is_error = True
        resp.json.return_value = {"message": f"Rate limit is exceeded. Try again in {wait} seconds."}
        return resp

    def _make_ok_resp(self) -> MagicMock:
        import json as _json
        resp = MagicMock()
        resp.status_code = 200
        resp.is_error = False
        resp.headers = {"content-type": "application/json"}
        resp.content = _json.dumps([{"country_code": "AGO"}]).encode()
        resp.text = _json.dumps([{"country_code": "AGO"}])
        resp.url = "https://api.worldbank.org/pip/v1/pip"
        resp.reason_phrase = "OK"
        return resp

    def test_succeeds_after_one_429(self, monkeypatch):
        """One 429 followed by a 200 must succeed (return the response)."""
        side_effects = [self._make_rate_limit_resp(), self._make_ok_resp()]
        call_count = 0

        def fake_get(url, params=None, **kwargs):
            nonlocal call_count
            result = side_effects[call_count]
            call_count += 1
            return result

        client = MagicMock()
        client.get.side_effect = fake_get
        monkeypatch.setattr("povineq._request.get_client", lambda server: client)
        monkeypatch.setattr("povineq._request.time.sleep", lambda s: None)

        resp = build_and_execute("pip", {})
        assert resp.status_code == 200
        assert client.get.call_count == 2

    def test_exhausted_retries_raises_rate_limit_error(self, monkeypatch):
        """All retries returning 429 must raise PIPRateLimitError."""
        client = MagicMock()
        client.get.return_value = self._make_rate_limit_resp(wait=5)
        monkeypatch.setattr("povineq._request.get_client", lambda server: client)
        monkeypatch.setattr("povineq._request.time.sleep", lambda s: None)

        with pytest.raises(PIPRateLimitError):
            build_and_execute("pip", {})

    def test_max_retry_seconds_cap_applied(self, monkeypatch):
        """Wait time is capped at _MAX_RETRY_SECONDS."""
        from povineq._request import _MAX_RETRY_SECONDS

        slept: list[float] = []
        side_effects = [self._make_rate_limit_resp(wait=9999), self._make_ok_resp()]
        call_count = 0

        def fake_get(*a, **kw):
            nonlocal call_count
            result = side_effects[min(call_count, len(side_effects) - 1)]
            call_count += 1
            return result

        client = MagicMock()
        client.get.side_effect = fake_get
        monkeypatch.setattr("povineq._request.get_client", lambda server: client)
        monkeypatch.setattr("povineq._request.time.sleep", lambda s: slept.append(s))

        build_and_execute("pip", {})
        assert slept[0] <= _MAX_RETRY_SECONDS


class TestConftestFixturesUsed:
    """P2.20 — ensure error_404_bytes and rate_limit_bytes conftest fixtures are exercised."""

    def test_parse_api_error_uses_404_fixture(self, error_404_bytes):
        """Verify the error_404_bytes fixture produces a valid PIPAPIError."""
        resp = MagicMock()
        resp.status_code = 404
        resp.reason_phrase = "Not Found"
        resp.json.return_value = __import__("json").loads(error_404_bytes)
        err = _parse_api_error(resp)
        assert err.status_code == 404
        assert "not valid" in err.details.lower() or "not found" in err.error_message.lower()

    def test_extract_retry_after_uses_rate_limit_fixture(self, rate_limit_bytes):
        """Verify the rate_limit_bytes fixture produces the expected wait time."""
        resp = MagicMock()
        resp.json.return_value = __import__("json").loads(rate_limit_bytes)
        wait = _extract_retry_after(resp)
        assert wait == pytest.approx(5.0)
