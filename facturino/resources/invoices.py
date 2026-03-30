"""Invoices resource — /v1/invoices

Supports full CRUD, finalize, send, cancel, remind, clone, PDF/Factur-X/XML
generation, status check, archive verification, events, audit trail,
payment links, and payment tokens.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Invoices:
    """Synchronous invoices resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft invoice.

        Args:
            customer: Customer ID.
            items: List of line items (description, quantity, unit_price, vat_rate).
            type: Invoice type (default "standard").
            dates: Dict with issued, due, serviceStart, serviceEnd.
            payment: Payment info (terms, method, etc.).
            notes: Free-text notes.
            metadata: Arbitrary key-value metadata.
            **params: Additional fields passed to the API.

        Returns:
            The created invoice dict.
        """
        # Map 'customer' to 'customerId' for API compatibility
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        # Accept both 'items' and 'lines'
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")

        resp = self._client.post("/v1/invoices", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/invoices", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, invoice_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/invoices/{invoice_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Only draft invoices can be updated. Finalized invoices are immutable."""
        body = dict(params)
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = self._client.patch(f"/v1/invoices/{invoice_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, invoice_id: str) -> None:
        self._client.delete(f"/v1/invoices/{invoice_id}")

    def finalize(self, invoice_id: str) -> dict[str, Any]:
        """Finalize an invoice: assign number, lock for editing, generate legal mentions."""
        resp = self._client.post(f"/v1/invoices/{invoice_id}/finalize")
        return resp.json()  # type: ignore[no-any-return]

    def send(self, invoice_id: str) -> dict[str, Any]:
        """Send a finalized invoice to the PA (e-invoicing platform).

        Returns 202 Accepted — the actual PA submission is asynchronous.
        """
        resp = self._client.post(f"/v1/invoices/{invoice_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    def cancel(self, invoice_id: str) -> dict[str, Any]:
        """Attempt to cancel an invoice.

        Note: Under French e-invoicing regulations, cancelling finalized
        invoices is not supported. Create a credit note instead.
        """
        resp = self._client.post(f"/v1/invoices/{invoice_id}/cancel")
        return resp.json()  # type: ignore[no-any-return]

    def remind(self, invoice_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/invoices/{invoice_id}/remind")
        return resp.json()  # type: ignore[no-any-return]

    def clone(self, invoice_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/invoices/{invoice_id}/clone")
        return resp.json()  # type: ignore[no-any-return]

    def get_pdf(self, invoice_id: str, *, template: str | None = None) -> dict[str, Any]:
        """Get or generate a PDF for an invoice.

        Returns either a signed download URL (if cached) or a 202 job object
        for async generation.
        """
        params: dict[str, Any] = {}
        if template:
            params["template"] = template
        resp = self._client.get(f"/v1/invoices/{invoice_id}/pdf", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_facturx(self, invoice_id: str, *, template: str | None = None) -> dict[str, Any]:
        """Get or generate a Factur-X PDF/A-3 document.

        Returns either a signed download URL or a 202 job object.
        """
        params: dict[str, Any] = {}
        if template:
            params["template"] = template
        resp = self._client.get(f"/v1/invoices/{invoice_id}/facturx", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_xml(self, invoice_id: str, *, format: str = "cii") -> Any:
        """Get the CII or UBL XML for an invoice.

        Args:
            invoice_id: Invoice ID.
            format: "cii" (default) or "ubl".

        Returns:
            XML string (Content-Type: application/xml).
        """
        resp = self._client.get(f"/v1/invoices/{invoice_id}/xml", params={"format": format})
        return resp.text

    def get_status(self, invoice_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/invoices/{invoice_id}/status")
        return resp.json()  # type: ignore[no-any-return]

    def verify(self, invoice_id: str) -> dict[str, Any]:
        """Verify the hash chain integrity of an archived invoice."""
        resp = self._client.get(f"/v1/invoices/{invoice_id}/verify")
        return resp.json()  # type: ignore[no-any-return]

    def list_events(self, invoice_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/invoices/{invoice_id}/events")
        return resp.json()  # type: ignore[no-any-return]

    def get_audit_trail(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.get(f"/v1/invoices/{invoice_id}/audit-trail", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def generate_audit_trail_pdf(self, invoice_id: str) -> dict[str, Any]:
        """Generate an audit trail PDF. Returns a 202 job object for async generation."""
        resp = self._client.post(f"/v1/invoices/{invoice_id}/audit-trail/pdf")
        return resp.json()  # type: ignore[no-any-return]

    def create_payment_link(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Create a Stripe payment link for an invoice (Pro+ only).

        Args:
            invoice_id: Invoice ID.
            success_url: URL to redirect after successful payment.
            cancel_url: URL to redirect after cancelled payment.
        """
        resp = self._client.post(f"/v1/invoices/{invoice_id}/payment-link", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def create_payment_token(self, invoice_id: str) -> dict[str, Any]:
        """Pro+ only."""
        resp = self._client.post(f"/v1/invoices/{invoice_id}/payment-token")
        return resp.json()  # type: ignore[no-any-return]

    def create_incoming(self, **params: Any) -> dict[str, Any]:
        """Create an incoming invoice (received from a supplier).

        Args:
            **params: Incoming invoice fields.

        Returns:
            The created incoming invoice dict.
        """
        resp = self._client.post("/v1/invoices/incoming", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def list_incoming(self, **params: Any) -> SyncPage:
        """List incoming invoices."""
        resp = self._client.get("/v1/invoices/incoming", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list_incoming, original_params=params)


class AsyncInvoices:
    """Asynchronous invoices resource.

    Supports full CRUD, finalize, send, cancel, remind, clone, PDF/Factur-X/XML
    generation, status check, archive verification, events, audit trail,
    payment links, and payment tokens.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft invoice.

        Args:
            customer: Customer ID.
            items: List of line items (description, quantity, unit_price, vat_rate).
            type: Invoice type (default "standard").
            dates: Dict with issued, due, serviceStart, serviceEnd.
            payment: Payment info (terms, method, etc.).
            notes: Free-text notes.
            metadata: Arbitrary key-value metadata.
            **params: Additional fields passed to the API.
        """
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = await self._client.post("/v1/invoices", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/invoices", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/invoices/{invoice_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Only draft invoices can be updated. Finalized invoices are immutable."""
        body = dict(params)
        if "items" in body and "lines" not in body:
            body["lines"] = body.pop("items")
        resp = await self._client.patch(f"/v1/invoices/{invoice_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, invoice_id: str) -> None:
        await self._client.delete(f"/v1/invoices/{invoice_id}")

    async def finalize(self, invoice_id: str) -> dict[str, Any]:
        """Assign number, lock for editing, generate legal mentions."""
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/finalize")
        return resp.json()  # type: ignore[no-any-return]

    async def send(self, invoice_id: str) -> dict[str, Any]:
        """Send a finalized invoice to the PA (e-invoicing platform).

        Returns 202 Accepted -- the actual PA submission is asynchronous.
        """
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    async def cancel(self, invoice_id: str) -> dict[str, Any]:
        """Attempt to cancel an invoice.

        Under French e-invoicing regulations, cancelling finalized
        invoices is not supported. Create a credit note instead.
        """
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/cancel")
        return resp.json()  # type: ignore[no-any-return]

    async def remind(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/remind")
        return resp.json()  # type: ignore[no-any-return]

    async def clone(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/clone")
        return resp.json()  # type: ignore[no-any-return]

    async def get_pdf(self, invoice_id: str, *, template: str | None = None) -> dict[str, Any]:
        """Get or generate a PDF for an invoice.

        Returns either a signed download URL (if cached) or a 202 job object
        for async generation.
        """
        params: dict[str, Any] = {}
        if template:
            params["template"] = template
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/pdf", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_facturx(self, invoice_id: str, *, template: str | None = None) -> dict[str, Any]:
        """Get or generate a Factur-X PDF/A-3 document.

        Returns either a signed download URL or a 202 job object.
        """
        params: dict[str, Any] = {}
        if template:
            params["template"] = template
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/facturx", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_xml(self, invoice_id: str, *, format: str = "cii") -> Any:
        """Get the CII or UBL XML for an invoice.

        Args:
            invoice_id: Invoice ID.
            format: "cii" (default) or "ubl".

        Returns:
            XML string (Content-Type: application/xml).
        """
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/xml", params={"format": format})
        return resp.text

    async def get_status(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/status")
        return resp.json()  # type: ignore[no-any-return]

    async def verify(self, invoice_id: str) -> dict[str, Any]:
        """Verify the hash chain integrity of an archived invoice."""
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/verify")
        return resp.json()  # type: ignore[no-any-return]

    async def list_events(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/events")
        return resp.json()  # type: ignore[no-any-return]

    async def get_audit_trail(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/invoices/{invoice_id}/audit-trail", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def generate_audit_trail_pdf(self, invoice_id: str) -> dict[str, Any]:
        """Generate an audit trail PDF. Returns a 202 job object for async generation."""
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/audit-trail/pdf")
        return resp.json()  # type: ignore[no-any-return]

    async def create_payment_link(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Create a Stripe payment link for an invoice (Pro+ only).

        Args:
            invoice_id: Invoice ID.
            success_url: URL to redirect after successful payment.
            cancel_url: URL to redirect after cancelled payment.
        """
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/payment-link", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def create_payment_token(self, invoice_id: str) -> dict[str, Any]:
        """Pro+ only."""
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/payment-token")
        return resp.json()  # type: ignore[no-any-return]

    async def create_incoming(self, **params: Any) -> dict[str, Any]:
        """Create an incoming invoice (received from a supplier).

        Args:
            **params: Incoming invoice fields.

        Returns:
            The created incoming invoice dict.
        """
        resp = await self._client.post("/v1/invoices/incoming", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def list_incoming(self, **params: Any) -> AsyncPage:
        """List incoming invoices."""
        resp = await self._client.get("/v1/invoices/incoming", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list_incoming, original_params=params)
