"""Payments resource — /v1/invoices/:invoiceId/payments

Payments are a sub-resource of invoices. Amounts are in integer centimes.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage
from .._types import Payment


class Payments:
    """Synchronous payments resource (sub-resource of invoices)."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, invoice_id: str, **params: Any) -> Payment:
        """Record a payment on an invoice.

        Args:
            invoice_id: The invoice to record payment against.
            amount: Payment amount in integer centimes (e.g. 10000 = 100.00 EUR).
            method: Payment method (transfer, card, check, cash, direct_debit, sepa, paypal).
            paid_at: ISO 8601 date when payment was received.
            reference: Optional payment reference.

        Returns:
            The created payment dict.
        """
        body = dict(params)
        # Accept snake_case alias
        if "paid_at" in body and "paidAt" not in body:
            body["paidAt"] = body.pop("paid_at")
        resp = self._client.post(f"/v1/invoices/{invoice_id}/payments", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, invoice_id: str, **params: Any) -> SyncPage:
        resp = self._client.get(f"/v1/invoices/{invoice_id}/payments", params=params)
        # Build fetcher that binds invoice_id
        def fetcher(**p: Any) -> SyncPage:
            return self.list(invoice_id, **p)
        return SyncPage.from_response(resp.json(), fetcher=fetcher, original_params=params)

    def cancel(self, invoice_id: str, payment_id: str) -> dict[str, Any]:
        """Cancel a recorded payment.

        The payment is kept for the audit trail (status ``cancelled``) and the
        invoice is re-settled from the reversal. Rejected once the payment has
        been reported to the tax authority.
        """
        resp = self._client.post(
            f"/v1/invoices/{invoice_id}/payments/{payment_id}/cancel"
        )
        return resp.json()  # type: ignore[no-any-return]


class AsyncPayments:
    """Asynchronous payments resource (sub-resource of invoices).

    Amounts are in integer centimes.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, invoice_id: str, **params: Any) -> Payment:
        """Record a payment on an invoice.

        Args:
            invoice_id: The invoice to record payment against.
            amount: Payment amount in integer centimes (e.g. 10000 = 100.00 EUR).
            method: Payment method (transfer, card, check, cash, direct_debit, sepa, paypal).
            paid_at: ISO 8601 date when payment was received.
            reference: Optional payment reference.
        """
        body = dict(params)
        if "paid_at" in body and "paidAt" not in body:
            body["paidAt"] = body.pop("paid_at")
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/payments", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, invoice_id: str, **params: Any) -> AsyncPage:
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/payments", params=params)
        async def fetcher(**p: Any) -> AsyncPage:
            return await self.list(invoice_id, **p)
        return AsyncPage.from_response(resp.json(), fetcher=fetcher, original_params=params)

    async def cancel(self, invoice_id: str, payment_id: str) -> dict[str, Any]:
        """Cancel a recorded payment.

        The payment is kept for the audit trail (status ``cancelled``) and the
        invoice is re-settled from the reversal. Rejected once the payment has
        been reported to the tax authority.
        """
        resp = await self._client.post(
            f"/v1/invoices/{invoice_id}/payments/{payment_id}/cancel"
        )
        return resp.json()  # type: ignore[no-any-return]
