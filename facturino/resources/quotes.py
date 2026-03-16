"""Quotes resource — /v1/quotes

CRUD + send, accept, refuse, convert to invoice, PDF generation.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Quotes:
    """Synchronous quotes resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft quote.

        Args:
            customer: Customer ID.
            items / lines: List of line items.
            dates: Dict with issued, validUntil.
            notes: Free-text notes.
        """
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = self._client.post("/v1/quotes", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/quotes", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, quote_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/quotes/{quote_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, quote_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = self._client.patch(f"/v1/quotes/{quote_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, quote_id: str) -> None:
        self._client.delete(f"/v1/quotes/{quote_id}")

    def send(self, quote_id: str) -> dict[str, Any]:
        """Assigns a number on first send."""
        resp = self._client.post(f"/v1/quotes/{quote_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    def accept(self, quote_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/quotes/{quote_id}/accept")
        return resp.json()  # type: ignore[no-any-return]

    def refuse(self, quote_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/quotes/{quote_id}/refuse")
        return resp.json()  # type: ignore[no-any-return]

    def convert(self, quote_id: str) -> dict[str, Any]:
        """Convert an accepted quote to a draft invoice. Returns the new invoice."""
        resp = self._client.post(f"/v1/quotes/{quote_id}/convert")
        return resp.json()  # type: ignore[no-any-return]

    def get_pdf(self, quote_id: str) -> Any:
        """Returns raw PDF bytes or a JSON dict depending on Content-Type."""
        resp = self._client.get(f"/v1/quotes/{quote_id}/pdf")
        content_type = resp.headers.get("content-type", "")
        if "application/pdf" in content_type:
            return resp.content
        return resp.json()


class AsyncQuotes:
    """Asynchronous quotes resource.

    CRUD + send, accept, refuse, convert to invoice, PDF generation.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft quote.

        Args:
            customer: Customer ID.
            items / lines: List of line items.
            dates: Dict with issued, validUntil.
            notes: Free-text notes.
        """
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = await self._client.post("/v1/quotes", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/quotes", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, quote_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/quotes/{quote_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, quote_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = await self._client.patch(f"/v1/quotes/{quote_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, quote_id: str) -> None:
        await self._client.delete(f"/v1/quotes/{quote_id}")

    async def send(self, quote_id: str) -> dict[str, Any]:
        """Assigns a number on first send."""
        resp = await self._client.post(f"/v1/quotes/{quote_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    async def accept(self, quote_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/quotes/{quote_id}/accept")
        return resp.json()  # type: ignore[no-any-return]

    async def refuse(self, quote_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/quotes/{quote_id}/refuse")
        return resp.json()  # type: ignore[no-any-return]

    async def convert(self, quote_id: str) -> dict[str, Any]:
        """Convert an accepted quote to a draft invoice. Returns the new invoice."""
        resp = await self._client.post(f"/v1/quotes/{quote_id}/convert")
        return resp.json()  # type: ignore[no-any-return]

    async def get_pdf(self, quote_id: str) -> Any:
        """Returns raw PDF bytes or a JSON dict depending on Content-Type."""
        resp = await self._client.get(f"/v1/quotes/{quote_id}/pdf")
        content_type = resp.headers.get("content-type", "")
        if "application/pdf" in content_type:
            return resp.content
        return resp.json()
