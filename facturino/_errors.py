"""Facturino API error classes.

All errors returned by the API follow the Stripe-like format:
    {
        "error": {
            "type": "invalid_request_error",
            "code": "resource_not_found",
            "message": "No such invoice: inv_xxx",
            "param": "id",
            "doc_url": "https://facturino.com/docs/api/errors#resource_not_found",
            "request_id": "req_xxx",
            "hint": "Check the invoice ID and try again."
        }
    }
"""

from __future__ import annotations

from typing import Any


class FacturinoError(Exception):
    """Base exception for all Facturino SDK errors."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class ApiError(FacturinoError):
    """Error returned by the Facturino API.

    Attributes:
        status_code: HTTP status code (e.g. 400, 404, 429).
        type: Error type (e.g. "invalid_request_error", "api_error").
        code: Machine-readable error code (e.g. "resource_not_found").
        param: The parameter that caused the error, if applicable.
        doc_url: Link to relevant documentation.
        request_id: Unique identifier for the request.
        hint: Human-readable suggestion for fixing the error.
        headers: HTTP response headers.
        body: Raw parsed response body.
    """

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int = 0,
        type: str = "",
        code: str = "",
        param: str | None = None,
        doc_url: str | None = None,
        request_id: str | None = None,
        hint: str | None = None,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.type = type
        self.code = code
        self.param = param
        self.doc_url = doc_url
        self.request_id = request_id
        self.hint = hint
        self.headers = headers or {}
        self.body = body

    def __repr__(self) -> str:
        return (
            f"ApiError(message={self.message!r}, status_code={self.status_code}, "
            f"type={self.type!r}, code={self.code!r})"
        )

    @classmethod
    def from_response(
        cls,
        status_code: int,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> ApiError:
        """Construct the appropriate error subclass from an API error response."""
        error_data = body.get("error", {})
        message = error_data.get("message", "Unknown error")
        error_type = error_data.get("type", "api_error")
        code = error_data.get("code", "")
        param = error_data.get("param")
        doc_url = error_data.get("doc_url")
        request_id = error_data.get("request_id")
        hint = error_data.get("hint")

        # Select the most specific error class
        error_cls: type[ApiError]
        if status_code == 401:
            error_cls = AuthenticationError
        elif status_code == 403:
            error_cls = PermissionDeniedError
        elif status_code == 404:
            error_cls = NotFoundError
        elif status_code == 402:
            error_cls = PlanLimitError
        elif status_code == 409:
            error_cls = ConflictError
        elif status_code == 422:
            error_cls = ValidationError
        elif status_code == 429:
            error_cls = RateLimitError
        elif status_code >= 500:
            error_cls = ServerError
        elif error_type == "invalid_request_error":
            error_cls = InvalidRequestError
        else:
            error_cls = cls

        return error_cls(
            message,
            status_code=status_code,
            type=error_type,
            code=code,
            param=param,
            doc_url=doc_url,
            request_id=request_id,
            hint=hint,
            headers=headers,
            body=body,
        )


class AuthenticationError(ApiError):
    """Raised when the API key is missing, invalid, or revoked (HTTP 401)."""


class PermissionDeniedError(ApiError):
    """Raised when the API key lacks the required permissions (HTTP 403)."""


class NotFoundError(ApiError):
    """Raised when a resource is not found (HTTP 404)."""


class InvalidRequestError(ApiError):
    """Raised when the request is malformed or has invalid parameters (HTTP 400)."""


class ValidationError(ApiError):
    """Raised when request body validation fails (HTTP 422)."""


class PlanLimitError(ApiError):
    """Raised when a feature is not available on the current plan (HTTP 402)."""


class ConflictError(ApiError):
    """Raised on resource conflicts, e.g. concurrent operations (HTTP 409)."""


class RateLimitError(ApiError):
    """Raised when the rate limit is exceeded (HTTP 429).

    Check ``retry_after`` for the number of seconds to wait before retrying.
    """

    @property
    def retry_after(self) -> float | None:
        """Seconds to wait before retrying, from the Retry-After header."""
        val = self.headers.get("retry-after")
        if val is not None:
            try:
                return float(val)
            except ValueError:
                pass
        return None


class ServerError(ApiError):
    """Raised on server-side errors (HTTP 5xx)."""


class SignatureVerificationError(FacturinoError):
    """Raised when webhook signature verification fails."""
