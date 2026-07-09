"""Billing resource — /v1/billing

Read the Stripe-backed subscription and list / download platform invoices.
Plan changes, checkout and the Customer Portal are handled in the Facturino
web app.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Billing:
    """Synchronous billing resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve_subscription(self) -> dict[str, Any]:
        """Current subscription (plan, cycle, status, period bounds)."""
        resp = self._client.get("/v1/billing/subscription")
        return resp.json()  # type: ignore[no-any-return]

    def list_invoices(self, **params: Any) -> dict[str, Any]:
        """Paginated list of platform invoices issued to this account."""
        resp = self._client.get("/v1/billing/invoices", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_invoice_pdf(self, invoice_id: str) -> dict[str, Any]:
        """Return a short-lived signed URL to download the PDF."""
        resp = self._client.get(f"/v1/billing/invoices/{invoice_id}/pdf")
        return resp.json()  # type: ignore[no-any-return]


class AsyncBilling:
    """Asynchronous billing resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve_subscription(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/billing/subscription")
        return resp.json()  # type: ignore[no-any-return]

    async def list_invoices(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.get("/v1/billing/invoices", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_invoice_pdf(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/billing/invoices/{invoice_id}/pdf")
        return resp.json()  # type: ignore[no-any-return]
