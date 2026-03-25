"""Received invoices resource — /v1/received-invoices

List, retrieve, approve, refuse, suspend, and record payments on incoming
invoices received from the PA (e-invoicing platform).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class ReceivedInvoices:
    """Synchronous received invoices resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        """List received invoices with cursor-based pagination.

        Args:
            status: Filter by status.
            limit: Max results per page (default 25, max 100).
            starting_after: Cursor for forward pagination.
            ending_before: Cursor for backward pagination.
        """
        resp = self._client.get("/v1/received-invoices", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def retrieve(self, received_invoice_id: str) -> dict[str, Any]:
        """Retrieve a received invoice by ID.

        Note: first retrieval auto-sends fr:204 lifecycle event to the PA.
        """
        resp = self._client.get(f"/v1/received-invoices/{received_invoice_id}")
        return resp.json()  # type: ignore[no-any-return]

    def approve(self, received_invoice_id: str) -> dict[str, Any]:
        """Approve a received invoice (sends fr:205 to PA).

        Valid from statuses: received, available, suspended.
        """
        resp = self._client.post(f"/v1/received-invoices/{received_invoice_id}/approve")
        return resp.json()  # type: ignore[no-any-return]

    def refuse(self, received_invoice_id: str, *, reason: str) -> dict[str, Any]:
        """Refuse a received invoice (sends fr:206 to PA).

        Args:
            received_invoice_id: The received invoice ID.
            reason: Mandatory refusal reason.

        Valid from statuses: received, available, suspended.
        """
        resp = self._client.post(
            f"/v1/received-invoices/{received_invoice_id}/refuse",
            json={"reason": reason},
        )
        return resp.json()  # type: ignore[no-any-return]

    def suspend(self, received_invoice_id: str) -> dict[str, Any]:
        """Suspend a received invoice (sends fr:207 to PA).

        Valid from statuses: received, available.
        """
        resp = self._client.post(f"/v1/received-invoices/{received_invoice_id}/suspend")
        return resp.json()  # type: ignore[no-any-return]

    def record_payment(
        self,
        received_invoice_id: str,
        *,
        amount: int,
        method: str | None = None,
        reference: str | None = None,
        paid_at: str | None = None,
    ) -> dict[str, Any]:
        """Record a payment on a received invoice (sends fr:212 to PA).

        Args:
            received_invoice_id: The received invoice ID.
            amount: Payment amount in integer centimes (e.g. 10000 = 100.00 EUR).
            method: Optional payment method (max 50 chars).
            reference: Optional payment reference (max 100 chars).
            paid_at: Optional ISO 8601 datetime when payment was received.
        """
        body: dict[str, Any] = {"amount": amount}
        if method is not None:
            body["method"] = method
        if reference is not None:
            body["reference"] = reference
        if paid_at is not None:
            body["paidAt"] = paid_at
        resp = self._client.post(
            f"/v1/received-invoices/{received_invoice_id}/record-payment",
            json=body,
        )
        return resp.json()  # type: ignore[no-any-return]


class AsyncReceivedInvoices:
    """Asynchronous received invoices resource.

    List, retrieve, approve, refuse, suspend, and record payments on incoming
    invoices received from the PA (e-invoicing platform).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        """List received invoices with cursor-based pagination."""
        resp = await self._client.get("/v1/received-invoices", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def retrieve(self, received_invoice_id: str) -> dict[str, Any]:
        """Retrieve a received invoice by ID.

        Note: first retrieval auto-sends fr:204 lifecycle event to the PA.
        """
        resp = await self._client.get(f"/v1/received-invoices/{received_invoice_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def approve(self, received_invoice_id: str) -> dict[str, Any]:
        """Approve a received invoice (sends fr:205 to PA).

        Valid from statuses: received, available, suspended.
        """
        resp = await self._client.post(f"/v1/received-invoices/{received_invoice_id}/approve")
        return resp.json()  # type: ignore[no-any-return]

    async def refuse(self, received_invoice_id: str, *, reason: str) -> dict[str, Any]:
        """Refuse a received invoice (sends fr:206 to PA).

        Args:
            received_invoice_id: The received invoice ID.
            reason: Mandatory refusal reason.

        Valid from statuses: received, available, suspended.
        """
        resp = await self._client.post(
            f"/v1/received-invoices/{received_invoice_id}/refuse",
            json={"reason": reason},
        )
        return resp.json()  # type: ignore[no-any-return]

    async def suspend(self, received_invoice_id: str) -> dict[str, Any]:
        """Suspend a received invoice (sends fr:207 to PA).

        Valid from statuses: received, available.
        """
        resp = await self._client.post(f"/v1/received-invoices/{received_invoice_id}/suspend")
        return resp.json()  # type: ignore[no-any-return]

    async def record_payment(
        self,
        received_invoice_id: str,
        *,
        amount: int,
        method: str | None = None,
        reference: str | None = None,
        paid_at: str | None = None,
    ) -> dict[str, Any]:
        """Record a payment on a received invoice (sends fr:212 to PA).

        Args:
            received_invoice_id: The received invoice ID.
            amount: Payment amount in integer centimes (e.g. 10000 = 100.00 EUR).
            method: Optional payment method (max 50 chars).
            reference: Optional payment reference (max 100 chars).
            paid_at: Optional ISO 8601 datetime when payment was received.
        """
        body: dict[str, Any] = {"amount": amount}
        if method is not None:
            body["method"] = method
        if reference is not None:
            body["reference"] = reference
        if paid_at is not None:
            body["paidAt"] = paid_at
        resp = await self._client.post(
            f"/v1/received-invoices/{received_invoice_id}/record-payment",
            json=body,
        )
        return resp.json()  # type: ignore[no-any-return]
