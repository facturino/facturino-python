"""Tests for the Facturino HTTP client: retries, error handling, headers."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

import facturino
from facturino._client import DEFAULT_BASE_URL, VERSION, SyncHttpClient
from facturino._errors import (
    AuthenticationError,
    FacturinoError,
    InvalidRequestError,
    NotFoundError,
    PlanLimitError,
    RateLimitError,
    ServerError,
)

API_KEY = "fac_test_abc123def456ghi789"
BASE = DEFAULT_BASE_URL


class TestClientInit:
    def test_requires_api_key(self):
        with pytest.raises(FacturinoError, match="API key is required"):
            facturino.Client("")

    def test_creates_resources(self):
        client = facturino.Client(API_KEY)
        assert hasattr(client, "invoices")
        assert hasattr(client, "customers")
        assert hasattr(client, "products")
        assert hasattr(client, "quotes")
        assert hasattr(client, "credit_notes")
        assert hasattr(client, "events")
        assert hasattr(client, "webhook_endpoints")
        assert hasattr(client, "recurring_invoices")
        assert hasattr(client, "companies")
        assert hasattr(client, "members")
        assert hasattr(client, "api_keys")
        assert hasattr(client, "exports")
        assert hasattr(client, "ereporting")
        assert hasattr(client, "jobs")
        assert hasattr(client, "sandbox")
        assert hasattr(client, "payments")
        client.close()

    def test_repr(self):
        client = facturino.Client(API_KEY)
        r = repr(client)
        assert "facturino.Client" in r
        assert "fac_test_abc" in r
        client.close()

    def test_context_manager(self):
        with facturino.Client(API_KEY) as client:
            assert client is not None

    def test_custom_base_url(self):
        client = facturino.Client(API_KEY, base_url="https://custom.example.com/api")
        assert client._http.base_url == "https://custom.example.com/api"
        client.close()


class TestHeaders:
    @respx.mock
    def test_sends_auth_header(self):
        route = respx.get(f"{BASE}/v1/test").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        http = SyncHttpClient(API_KEY)
        http.get("/v1/test")

        assert route.called
        request = route.calls[0].request
        assert request.headers["authorization"] == f"Bearer {API_KEY}"
        assert request.headers["user-agent"] == f"facturino-python/{VERSION}"
        assert request.headers["accept"] == "application/json"
        http.close()

    @respx.mock
    def test_sends_idempotency_key_on_post(self):
        route = respx.post(f"{BASE}/v1/test").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        http = SyncHttpClient(API_KEY)
        http.post("/v1/test", json={"key": "value"})

        request = route.calls[0].request
        assert "idempotency-key" in request.headers
        http.close()

    @respx.mock
    def test_custom_idempotency_key(self):
        route = respx.post(f"{BASE}/v1/test").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        http = SyncHttpClient(API_KEY)
        http.post("/v1/test", json={}, idempotency_key="my-key-123")

        request = route.calls[0].request
        assert request.headers["idempotency-key"] == "my-key-123"
        http.close()

    @respx.mock
    def test_no_idempotency_key_on_get(self):
        route = respx.get(f"{BASE}/v1/test").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        http = SyncHttpClient(API_KEY)
        http.get("/v1/test")

        request = route.calls[0].request
        assert "idempotency-key" not in request.headers
        http.close()


class TestErrorHandling:
    @respx.mock
    def test_401_raises_authentication_error(self):
        respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(401, json={
                "error": {
                    "type": "authentication_error",
                    "code": "invalid_api_key",
                    "message": "Invalid API key",
                }
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(AuthenticationError) as exc_info:
            http.get("/v1/invoices")
        assert exc_info.value.status_code == 401
        assert exc_info.value.code == "invalid_api_key"
        http.close()

    @respx.mock
    def test_404_raises_not_found_error(self):
        respx.get(f"{BASE}/v1/invoices/inv_missing").mock(
            return_value=httpx.Response(404, json={
                "error": {
                    "type": "invalid_request_error",
                    "code": "resource_not_found",
                    "message": "No such invoice: inv_missing",
                    "param": "id",
                    "doc_url": "https://facturino.com/docs/api/errors#resource_not_found",
                    "request_id": "req_abc123",
                    "hint": "Check the invoice ID.",
                }
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(NotFoundError) as exc_info:
            http.get("/v1/invoices/inv_missing")

        err = exc_info.value
        assert err.status_code == 404
        assert err.code == "resource_not_found"
        assert err.param == "id"
        assert err.doc_url == "https://facturino.com/docs/api/errors#resource_not_found"
        assert err.request_id == "req_abc123"
        assert err.hint == "Check the invoice ID."
        http.close()

    @respx.mock
    def test_400_raises_invalid_request_error(self):
        respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(400, json={
                "error": {
                    "type": "invalid_request_error",
                    "code": "missing_required_field",
                    "message": "customerId is required",
                    "param": "customerId",
                }
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(InvalidRequestError):
            http.post("/v1/invoices", json={})
        http.close()

    @respx.mock
    def test_402_raises_plan_limit_error(self):
        respx.post(f"{BASE}/v1/exports/fec").mock(
            return_value=httpx.Response(402, json={
                "error": {
                    "type": "invalid_request_error",
                    "code": "plan_limit",
                    "message": "FEC export requires Pro plan",
                }
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(PlanLimitError):
            http.post("/v1/exports/fec", json={})
        http.close()

    @respx.mock
    def test_429_raises_rate_limit_error(self):
        respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(429, json={
                "error": {
                    "type": "api_error",
                    "code": "rate_limit_exceeded",
                    "message": "Rate limit exceeded",
                }
            }, headers={"retry-after": "5"})
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(RateLimitError) as exc_info:
            http.get("/v1/invoices")
        assert exc_info.value.retry_after == 5.0
        http.close()

    @respx.mock
    def test_500_raises_server_error(self):
        respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(500, json={
                "error": {
                    "type": "api_error",
                    "code": "internal_error",
                    "message": "Internal server error",
                }
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=0)
        with pytest.raises(ServerError):
            http.get("/v1/invoices")
        http.close()


class TestRetries:
    @respx.mock
    def test_retries_on_500(self):
        route = respx.get(f"{BASE}/v1/invoices")
        route.side_effect = [
            httpx.Response(500, json={"error": {"type": "api_error", "message": "Server error"}}),
            httpx.Response(200, json={"object": "list", "data": []}),
        ]

        http = SyncHttpClient(API_KEY, max_retries=1)
        with patch("facturino._client.time.sleep"):
            resp = http.get("/v1/invoices")

        assert resp.status_code == 200
        assert route.call_count == 2
        http.close()

    @respx.mock
    def test_retries_on_429_with_retry_after(self):
        route = respx.get(f"{BASE}/v1/invoices")
        route.side_effect = [
            httpx.Response(
                429,
                json={"error": {"type": "api_error", "message": "Rate limited"}},
                headers={"retry-after": "1"},
            ),
            httpx.Response(200, json={"object": "list", "data": []}),
        ]

        http = SyncHttpClient(API_KEY, max_retries=1)
        with patch("facturino._client.time.sleep") as mock_sleep:
            resp = http.get("/v1/invoices")

        assert resp.status_code == 200
        mock_sleep.assert_called_once_with(1.0)
        http.close()

    @respx.mock
    def test_retries_on_502(self):
        route = respx.get(f"{BASE}/v1/invoices")
        route.side_effect = [
            httpx.Response(502, json={"error": {"type": "api_error", "message": "Bad gateway"}}),
            httpx.Response(200, json={"object": "list", "data": []}),
        ]

        http = SyncHttpClient(API_KEY, max_retries=1)
        with patch("facturino._client.time.sleep"):
            resp = http.get("/v1/invoices")

        assert resp.status_code == 200
        http.close()

    @respx.mock
    def test_exhausted_retries_raises(self):
        respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(500, json={"error": {"type": "api_error", "message": "Down"}})
        )

        http = SyncHttpClient(API_KEY, max_retries=2)
        with patch("facturino._client.time.sleep"):
            with pytest.raises(ServerError):
                http.get("/v1/invoices")
        http.close()

    @respx.mock
    def test_no_retry_on_400(self):
        route = respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(400, json={
                "error": {"type": "invalid_request_error", "message": "Bad request"}
            })
        )

        http = SyncHttpClient(API_KEY, max_retries=3)
        with pytest.raises(InvalidRequestError):
            http.post("/v1/invoices", json={})

        assert route.call_count == 1
        http.close()


class TestParamsFiltering:
    @respx.mock
    def test_filters_none_params(self):
        route = respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [],
                    "has_more": False,
                    "next_cursor": None,
                    "url": "/v1/invoices",
                },
            )
        )

        http = SyncHttpClient(API_KEY)
        http.get("/v1/invoices", params={"limit": 10, "status": None, "starting_after": None})

        request = route.calls[0].request
        assert "status" not in str(request.url)
        assert "starting_after" not in str(request.url)
        assert "limit=10" in str(request.url)
        http.close()
