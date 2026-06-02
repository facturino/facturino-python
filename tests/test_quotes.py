"""Tests for the Quotes resource."""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino
from facturino._client import DEFAULT_BASE_URL

API_KEY = "fac_test_abc123def456ghi789"
BASE = DEFAULT_BASE_URL


@pytest.fixture
def client():
    c = facturino.Client(API_KEY)
    yield c
    c.close()


class TestQuoteClone:
    @respx.mock
    def test_clone(self, client):
        respx.post(f"{BASE}/v1/quotes/quo_1/clone").mock(
            return_value=httpx.Response(201, json={
                "id": "quo_clone_1",
                "object": "quote",
                "status": "draft",
            })
        )

        result = client.quotes.clone("quo_1")
        assert result["id"] == "quo_clone_1"
        assert result["status"] == "draft"

    @respx.mock
    def test_clone_targets_clone_endpoint(self, client):
        route = respx.post(f"{BASE}/v1/quotes/quo_1/clone").mock(
            return_value=httpx.Response(201, json={"id": "quo_clone_1", "object": "quote"})
        )

        client.quotes.clone("quo_1")

        assert route.called
        assert route.calls[0].request.url.path.endswith("/v1/quotes/quo_1/clone")


class TestQuoteActions:
    @respx.mock
    def test_convert(self, client):
        respx.post(f"{BASE}/v1/quotes/quo_1/convert").mock(
            return_value=httpx.Response(201, json={
                "id": "inv_from_quo",
                "object": "invoice",
                "status": "draft",
            })
        )

        result = client.quotes.convert("quo_1")
        assert result["id"] == "inv_from_quo"

    @respx.mock
    def test_send(self, client):
        respx.post(f"{BASE}/v1/quotes/quo_1/send").mock(
            return_value=httpx.Response(200, json={
                "id": "quo_1",
                "object": "quote",
                "status": "sent",
                "number": "DEV-2026-00001",
            })
        )

        result = client.quotes.send("quo_1")
        assert result["status"] == "sent"


@pytest.mark.asyncio
class TestAsyncQuoteClone:
    @respx.mock
    async def test_clone(self):
        respx.post(f"{BASE}/v1/quotes/quo_1/clone").mock(
            return_value=httpx.Response(201, json={
                "id": "quo_clone_1",
                "object": "quote",
                "status": "draft",
            })
        )

        async with facturino.AsyncClient(API_KEY) as client:
            result = await client.quotes.clone("quo_1")

        assert result["id"] == "quo_clone_1"
        assert result["status"] == "draft"
