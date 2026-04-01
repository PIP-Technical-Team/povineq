"""Custom exceptions for the povineq package."""

from __future__ import annotations


class PIPError(Exception):
    """Base exception for all PIP API errors."""


class PIPAPIError(PIPError):
    """API returned a structured error response (4xx/5xx).

    Attributes:
        status_code: HTTP status code of the response.
        error_message: Short error description from the API.
        details: Additional detail message, if provided.
        valid_values: Comma-separated valid values, if provided.
    """

    def __init__(
        self,
        status_code: int,
        error_message: str = "",
        details: str = "",
        valid_values: str = "",
    ) -> None:
        self.status_code = status_code
        self.error_message = error_message
        self.details = details
        self.valid_values = valid_values
        parts = [p for p in [error_message, details, valid_values] if p]
        super().__init__(f"HTTP {status_code}: {' | '.join(parts)}")


class PIPRateLimitError(PIPError):
    """API rate limit exceeded (HTTP 429).

    Attributes:
        retry_after_seconds: Suggested wait time in seconds before retrying.
    """

    def __init__(self, retry_after_seconds: float = 0) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after_seconds:.0f} seconds."
        )


class PIPConnectionError(PIPError):
    """Network connectivity issue — cannot reach the API."""


class PIPValidationError(PIPError):
    """Invalid parameter values detected before the API call."""
