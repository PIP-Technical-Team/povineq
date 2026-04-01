"""Tests for _errors.py."""

from __future__ import annotations

import pytest

from povineq._errors import (
    PIPAPIError,
    PIPConnectionError,
    PIPError,
    PIPRateLimitError,
    PIPValidationError,
)


def test_pip_error_is_base():
    err = PIPError("base error")
    assert isinstance(err, Exception)
    assert str(err) == "base error"


def test_pip_api_error_stores_fields():
    err = PIPAPIError(404, "Not found", "Country XYZ invalid", "AGO, ALB")
    assert err.status_code == 404
    assert err.error_message == "Not found"
    assert err.details == "Country XYZ invalid"
    assert err.valid_values == "AGO, ALB"
    assert "404" in str(err)
    assert "Not found" in str(err)


def test_pip_api_error_minimal():
    err = PIPAPIError(500)
    assert err.status_code == 500
    assert err.error_message == ""
    assert "500" in str(err)


def test_pip_rate_limit_error():
    err = PIPRateLimitError(30)
    assert err.retry_after_seconds == 30
    assert "30" in str(err)


def test_pip_rate_limit_default():
    err = PIPRateLimitError()
    assert err.retry_after_seconds == 0


def test_pip_connection_error():
    err = PIPConnectionError("no internet")
    assert isinstance(err, PIPError)
    assert "no internet" in str(err)


def test_pip_validation_error():
    err = PIPValidationError("invalid country code")
    assert isinstance(err, PIPError)


def test_exception_hierarchy():
    assert issubclass(PIPAPIError, PIPError)
    assert issubclass(PIPRateLimitError, PIPError)
    assert issubclass(PIPConnectionError, PIPError)
    assert issubclass(PIPValidationError, PIPError)


def test_can_be_raised_and_caught():
    with pytest.raises(PIPError):
        raise PIPAPIError(404, "test")

    with pytest.raises(PIPAPIError):
        raise PIPAPIError(404, "test")
