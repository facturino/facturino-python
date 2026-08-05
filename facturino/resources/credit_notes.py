"""Credit notes resource — /v1/credit-notes

CRUD + finalize, send, PDF and Factur-X generation.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


def _email_body(params: dict[str, Any]) -> dict[str, Any]:
    """Build the `/email` request body.

    Accepts both snake_case (Pythonic) and camelCase (API-style) kwargs
    so callers can stay idiomatic locally while the HTTP payload always
    matches the Zod schema documented at ``/docs/credit-notes#email``.
    """
    body: dict[str, Any] = {}
    for snake, camel in (
        ("recipient_email", "recipientEmail"),
        ("custom_message", "customMessage"),
        ("include_xml", "includeXml"),
        ("custom_subject", "customSubject"),
    ):
        if snake in params:
            body[camel] = params[snake]
        elif camel in params:
            body[camel] = params[camel]
    return body


class CreditNotes:
    """Synchronous credit notes resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft credit note.

        Args:
            customer: Customer ID.
            related_invoice_id / relatedInvoiceId: Original invoice ID.
            credit_note_type / creditNoteType: Type of credit note.
            reason_code / reasonCode: Reason code (defective_goods, duplicate, quality, other).
            reason: Free-text reason.
            items: List of line items.
            dates: Dict with issued date.
            notes: Free-text notes.
        """
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        if "related_invoice_id" in body and "relatedInvoiceId" not in body:
            body["relatedInvoiceId"] = body.pop("related_invoice_id")
        if "credit_note_type" in body and "creditNoteType" not in body:
            body["creditNoteType"] = body.pop("credit_note_type")
        if "reason_code" in body and "reasonCode" not in body:
            body["reasonCode"] = body.pop("reason_code")
        resp = self._client.post("/v1/credit-notes", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/credit-notes", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, credit_note_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/credit-notes/{credit_note_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(f"/v1/credit-notes/{credit_note_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, credit_note_id: str) -> None:
        self._client.delete(f"/v1/credit-notes/{credit_note_id}")

    def finalize(self, credit_note_id: str) -> dict[str, Any]:
        """Assign number and lock for editing."""
        resp = self._client.post(f"/v1/credit-notes/{credit_note_id}/finalize")
        return resp.json()  # type: ignore[no-any-return]

    def send(self, credit_note_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/credit-notes/{credit_note_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    def email(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        """Send the credit note by email with the PDF attached.

        Returns ``{"status": "sent", ...}`` once dispatched, or
        ``{"status": "pending", "jobId": …}`` when the PDF is still
        being rendered (caller should poll the returned job).

        Args:
            recipient_email / recipientEmail: Override recipient address.
            custom_message / customMessage: Personal message body.
            include_xml / includeXml: When ``True``, also attach the XML CII.
            custom_subject / customSubject: Override default subject line.
        """
        resp = self._client.post(
            f"/v1/credit-notes/{credit_note_id}/email", json=_email_body(params)
        )
        return resp.json()  # type: ignore[no-any-return]

    def refund(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        """Record the disbursement of a finalized credit note back to the customer.

        Writes a negative ``refund`` payment on the linked invoice.

        Args:
            amount: Amount in integer centimes (defaults to the full credit-note total).
            method: Payment method (transfer, card, check, cash, direct_debit, sepa, paypal).
            refunded_at / refundedAt: ISO date of the disbursement.

        Returns:
            ``{"object": "refund", "id": …, "creditNoteId": …, "invoiceId": …, "amount": …}``.
        """
        body: dict[str, Any] = {}
        if "amount" in params:
            body["amount"] = params["amount"]
        if "method" in params:
            body["method"] = params["method"]
        if "refunded_at" in params:
            body["refundedAt"] = params["refunded_at"]
        elif "refundedAt" in params:
            body["refundedAt"] = params["refundedAt"]
        resp = self._client.post(f"/v1/credit-notes/{credit_note_id}/refund", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def get_pdf(self, credit_note_id: str) -> Any:
        """Returns raw PDF bytes or a JSON dict depending on Content-Type."""
        resp = self._client.get(f"/v1/credit-notes/{credit_note_id}/pdf")
        content_type = resp.headers.get("content-type", "")
        if "application/pdf" in content_type:
            return resp.content
        return resp.json()

    def get_facturx(self, credit_note_id: str) -> dict[str, Any]:
        """Get or generate a Factur-X PDF/A-3 document for a credit note.

        Returns either a signed download URL or a 202 job object.
        """
        resp = self._client.get(f"/v1/credit-notes/{credit_note_id}/facturx")
        return resp.json()  # type: ignore[no-any-return]

    def get_xml(self, credit_note_id: str, *, format: str = "cii") -> Any:
        """Get the CII or UBL XML for a credit note.

        Args:
            credit_note_id: Credit note ID.
            format: "cii" (default) or "ubl".

        Returns:
            XML string (Content-Type: application/xml).
        """
        resp = self._client.get(f"/v1/credit-notes/{credit_note_id}/xml", params={"format": format})
        return resp.text


class AsyncCreditNotes:
    """Asynchronous credit notes resource.

    CRUD + finalize, send, PDF and Factur-X generation.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a draft credit note.

        Args:
            customer: Customer ID.
            related_invoice_id / relatedInvoiceId: Original invoice ID.
            credit_note_type / creditNoteType: Type of credit note.
            reason_code / reasonCode: Reason code (defective_goods, duplicate, quality, other).
            reason: Free-text reason.
            items: List of line items.
            dates: Dict with issued date.
            notes: Free-text notes.
        """
        body = dict(params)
        if "customer" in body and "customerId" not in body:
            body["customerId"] = body.pop("customer")
        if "related_invoice_id" in body and "relatedInvoiceId" not in body:
            body["relatedInvoiceId"] = body.pop("related_invoice_id")
        if "credit_note_type" in body and "creditNoteType" not in body:
            body["creditNoteType"] = body.pop("credit_note_type")
        if "reason_code" in body and "reasonCode" not in body:
            body["reasonCode"] = body.pop("reason_code")
        resp = await self._client.post("/v1/credit-notes", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/credit-notes", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, credit_note_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/credit-notes/{credit_note_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/credit-notes/{credit_note_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, credit_note_id: str) -> None:
        await self._client.delete(f"/v1/credit-notes/{credit_note_id}")

    async def finalize(self, credit_note_id: str) -> dict[str, Any]:
        """Assign number and lock for editing."""
        resp = await self._client.post(f"/v1/credit-notes/{credit_note_id}/finalize")
        return resp.json()  # type: ignore[no-any-return]

    async def send(self, credit_note_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/credit-notes/{credit_note_id}/send")
        return resp.json()  # type: ignore[no-any-return]

    async def email(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        """Send the credit note by email with the PDF attached.

        See :meth:`CreditNotes.email` for the parameter and return shape.
        """
        resp = await self._client.post(
            f"/v1/credit-notes/{credit_note_id}/email", json=_email_body(params)
        )
        return resp.json()  # type: ignore[no-any-return]

    async def refund(self, credit_note_id: str, **params: Any) -> dict[str, Any]:
        """Record the disbursement of a finalized credit note back to the customer.

        See :meth:`CreditNotes.refund` for the parameter and return shape.
        """
        body: dict[str, Any] = {}
        if "amount" in params:
            body["amount"] = params["amount"]
        if "method" in params:
            body["method"] = params["method"]
        if "refunded_at" in params:
            body["refundedAt"] = params["refunded_at"]
        elif "refundedAt" in params:
            body["refundedAt"] = params["refundedAt"]
        resp = await self._client.post(f"/v1/credit-notes/{credit_note_id}/refund", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def get_pdf(self, credit_note_id: str) -> Any:
        """Returns raw PDF bytes or a JSON dict depending on Content-Type."""
        resp = await self._client.get(f"/v1/credit-notes/{credit_note_id}/pdf")
        content_type = resp.headers.get("content-type", "")
        if "application/pdf" in content_type:
            return resp.content
        return resp.json()

    async def get_facturx(self, credit_note_id: str) -> dict[str, Any]:
        """Get or generate a Factur-X PDF/A-3 document for a credit note.

        Returns either a signed download URL or a 202 job object.
        """
        resp = await self._client.get(f"/v1/credit-notes/{credit_note_id}/facturx")
        return resp.json()  # type: ignore[no-any-return]

    async def get_xml(self, credit_note_id: str, *, format: str = "cii") -> Any:
        """Get the CII or UBL XML for a credit note.

        Args:
            credit_note_id: Credit note ID.
            format: "cii" (default) or "ubl".

        Returns:
            XML string (Content-Type: application/xml).
        """
        resp = await self._client.get(f"/v1/credit-notes/{credit_note_id}/xml", params={"format": format})
        return resp.text
