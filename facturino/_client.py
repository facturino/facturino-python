"""Low-level HTTP client for the Facturino API.

Handles authentication, retries with exponential backoff, error parsing,
idempotency keys, and response deserialization.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx

from ._errors import ApiError, FacturinoError

# SDK metadata
VERSION = "1.0.1"
API_VERSION = "2026-03-01"
DEFAULT_BASE_URL = "https://facturino.com/api"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_STATUS_CODES = {429, 500, 502, 503}
INITIAL_RETRY_DELAY = 0.5  # seconds
MAX_RETRY_DELAY = 30.0  # seconds


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"facturino-python/{VERSION}",
        "Facturino-Version": API_VERSION,
    }


def _parse_error_response(response: httpx.Response) -> ApiError:
    """Parse an error response into the appropriate ApiError subclass."""
    headers = dict(response.headers)
    try:
        body = response.json()
    except Exception:
        body = {"error": {"type": "api_error", "message": response.text or "Unknown error"}}

    return ApiError.from_response(response.status_code, body, headers)


def _get_retry_delay(attempt: int, response: httpx.Response | None = None) -> float:
    """Compute retry delay using exponential backoff, respecting Retry-After."""
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after is not None:
            try:
                return min(float(retry_after), MAX_RETRY_DELAY)
            except ValueError:
                pass

    delay = INITIAL_RETRY_DELAY * (2 ** attempt)
    return min(float(delay), MAX_RETRY_DELAY)


class SyncHttpClient:
    """Synchronous HTTP client with retry logic."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=_build_headers(api_key),
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SyncHttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with automatic retries on transient failures."""
        extra_headers: dict[str, str] = {}
        if headers:
            extra_headers.update(headers)

        # A caller may pass idempotency_key as a body field (resource methods
        # forward **params straight to the JSON body). Lift it into the header
        # so it controls idempotency instead of being rejected as an unknown
        # body field by the strict API schema.
        if idempotency_key is None and isinstance(json, dict) and "idempotency_key" in json:
            json = dict(json)
            idempotency_key = json.pop("idempotency_key")

        # Auto-generate idempotency key for POST requests
        if method.upper() == "POST" and idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        if idempotency_key:
            extra_headers["Idempotency-Key"] = idempotency_key

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Exception | None = None
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                    headers=extra_headers,
                )
                last_response = response

                if response.status_code < 400:
                    return response

                if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries:
                    delay = _get_retry_delay(attempt, response)
                    time.sleep(delay)
                    continue

                raise _parse_error_response(response)

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = _get_retry_delay(attempt)
                    time.sleep(delay)
                    continue
                raise FacturinoError(f"Connection failed after {self.max_retries + 1} attempts: {exc}") from exc

        # Fallback after exhausting all retry attempts
        if last_response is not None:
            raise _parse_error_response(last_response)
        raise FacturinoError("Request failed") from last_error

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)


class AsyncHttpClient:
    """Asynchronous HTTP client with retry logic."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_build_headers(api_key),
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request with automatic retries."""
        extra_headers: dict[str, str] = {}
        if headers:
            extra_headers.update(headers)

        # Lift a body-level idempotency_key into the header (see sync request()).
        if idempotency_key is None and isinstance(json, dict) and "idempotency_key" in json:
            json = dict(json)
            idempotency_key = json.pop("idempotency_key")

        if method.upper() == "POST" and idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        if idempotency_key:
            extra_headers["Idempotency-Key"] = idempotency_key

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Exception | None = None
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                    headers=extra_headers,
                )
                last_response = response

                if response.status_code < 400:
                    return response

                if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries:
                    delay = _get_retry_delay(attempt, response)
                    await asyncio.sleep(delay)
                    continue

                raise _parse_error_response(response)

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = _get_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise FacturinoError(f"Connection failed after {self.max_retries + 1} attempts: {exc}") from exc

        if last_response is not None:
            raise _parse_error_response(last_response)
        raise FacturinoError("Request failed") from last_error

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)
