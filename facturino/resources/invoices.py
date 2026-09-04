"""Invoices resource — /v1/invoices

Supports full CRUD, finalize, send, cancel, remind, clone, PDF/Factur-X/XML
generation, status check, archive verification, events, audit trail,
payment links, and payment tokens.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


def _build_invoice_create_body(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize aliases and enforce the decision-first contract locally."""
    body = dict(params)
    if "customer" in body and "customerId" not in body:
        body["customerId"] = body.pop("customer")
    if "tax_decision_id" in body and "taxDecisionId" not in body:
        body["taxDecisionId"] = body.pop("tax_decision_id")
    if "decision_lines" in body and "decisionLines" not in body:
        body["decisionLines"] = body.pop("decision_lines")

    for removed in ("items", "lines"):
        # PRESENCE of the key is refused — an empty list included: it states
        # the intent to restate VAT on the invoice, which no contract allows.
        if removed in body:
            raise ValueError(
                f"'{removed}' is not part of the invoice contract: an invoice "
                "never states its own VAT. Create a tax decision first "
                "(client.tax_decisions.create), then reference it with "
                "'taxDecisionId' and describe the document lines with "
                "'decisionLines'."
            )
    tax_decision_id = body.get("taxDecisionId")
    if not isinstance(tax_decision_id, str) or not tax_decision_id:
        raise ValueError(
            "'taxDecisionId' is required: every invoice is created from an "
            "immutable tax decision (POST /v1/tax-decisions)."
        )
    decision_lines = body.get("decisionLines")
    if not isinstance(decision_lines, list) or not decision_lines:
        raise ValueError(
            "'decisionLines' is required and non-empty: each entry references "
            "a decision line by 'taxLineRef' and completes the document-only "
            "details (unit, product)."
        )
    return body



def _build_finalize_body(payment: dict[str, Any] | None) -> dict[str, Any] | None:
    """Body of a finalization: absent, or the collection received before issuance.

    ``paid_at`` is accepted as a snake_case alias, exactly as
    :meth:`Payments.create` accepts it — the two surfaces take the same object.
    """
    if payment is None:
        return None
    body = dict(payment)
    if "paid_at" in body and "paidAt" not in body:
        body["paidAt"] = body.pop("paid_at")
    return {"payment": body}


def _build_bind_decision_body(params: dict[str, Any]) -> dict[str, Any]:
    """Normalize aliases and enforce the binding contract locally.

    Binding carries the decision and the presentation of its lines, and nothing
    else: the draft already states the buyer, the dates and the payment terms,
    and the decision states the whole fiscal content.
    """
    body = dict(params)
    if "tax_decision_id" in body and "taxDecisionId" not in body:
        body["taxDecisionId"] = body.pop("tax_decision_id")
    if "decision_lines" in body and "decisionLines" not in body:
        body["decisionLines"] = body.pop("decision_lines")

    tax_decision_id = body.get("taxDecisionId")
    if not isinstance(tax_decision_id, str) or not tax_decision_id:
        raise ValueError(
            "'taxDecisionId' is required: a commercial draft is fiscalised by "
            "binding a FINAL tax decision to it (POST /v1/tax-decisions)."
        )
    decision_lines = body.get("decisionLines")
    if not isinstance(decision_lines, list) or not decision_lines:
        raise ValueError(
            "'decisionLines' is required and non-empty: each entry references "
            "a decision line by 'taxLineRef' and completes the document-only "
            "details (unit, product)."
        )
    return body


class Invoices:
    """Synchronous invoices resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(
        self, *, idempotency_key: str | None = None, **params: Any
    ) -> dict[str, Any]:
        """Create a draft invoice from an immutable tax decision.

        Every invoice references the decision that fixed its VAT and its
        amounts; the invoice never restates a rate. ``items``/``lines`` are
        refused locally, before any HTTP call.

        Args:
            customer: Customer ID.
            tax_decision_id / taxDecisionId: The final decision backing this
                invoice. One decision creates exactly one invoice.
            decision_lines / decisionLines: One entry per decision line —
                ``taxLineRef`` plus the document-only details (``unit``,
                ``product``).
            type: Invoice type (default "standard").
            buyer: Buyer identity snapshot.
            dates: Dict with issued, due, serviceStart, serviceEnd.
            payment: Payment info (terms, method, etc.).
            deposits: Fully paid deposit invoices deducted from this balance
                invoice, settled server-side against the DECIDED amount.
            schedule: Instalments in integer cents; they must distribute
                exactly the decided amount due.
            notes: Free-text notes.
            metadata: Arbitrary key-value metadata.
            **params: Additional fields passed to the API.

        Returns:
            The created invoice dict.
        """
        body = _build_invoice_create_body(params)
        resp = self._client.post(
            "/v1/invoices", json=body, idempotency_key=idempotency_key
        )
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        """List invoices.

        Args:
            status: Filter by lifecycle status.
            customerId: Filter by customer ID.
            convertedFrom: Filter by source quote ID (a ``quo_…`` string);
                returns only the invoices converted from that quote.
            limit / starting_after: Pagination controls.
            **params: Any other supported query filter.
        """
        resp = self._client.get("/v1/invoices", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Retrieve an invoice.

        Args:
            invoice_id: Invoice ID.
            expand: Comma-separated relations to inline, among
                ``customer``, ``items.product`` and ``credit_notes``. With
                ``expand="credit_notes"`` the response carries an
                ``expanded.credit_notes`` array and an ``expanded.net_balance``
                string (TTC minus issued credit notes).
            **params: Any other supported query parameter.
        """
        resp = self._client.get(f"/v1/invoices/{invoice_id}", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def update(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Update a draft invoice's non-fiscal fields.

        Only drafts can be updated, and only ``dates``, ``payment``, ``notes``,
        ``purchaseOrderNumber`` and ``metadata``: the commercial operation and
        its VAT belong to the decision, which is immutable. To change the
        operation, take a new decision and create a new draft.
        """
        resp = self._client.patch(f"/v1/invoices/{invoice_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, invoice_id: str) -> None:
        self._client.delete(f"/v1/invoices/{invoice_id}")

    def bind_tax_decision(
        self, invoice_id: str, *, idempotency_key: str | None = None, **params: Any
    ) -> dict[str, Any]:
        """Bind a FINAL tax decision to a commercial draft that already exists.

        This closes the quote cycle on ONE document::

            converted = client.quotes.convert(quote_id)
            decision = client.tax_decisions.create(idempotency_key=key, ...)
            client.invoices.bind_tax_decision(
                converted["invoiceId"],
                tax_decision_id=decision["id"],
                decision_lines=[{"taxLineRef": "l1", "unit": "unit"}],
            )
            client.invoices.finalize(converted["invoiceId"])

        The invoice stays a DRAFT: binding freezes the VAT, ``finalize`` issues
        it. Idempotent on the decision — replaying the same call returns the
        same invoice.

        Args:
            invoice_id: The commercial draft to fiscalise.
            tax_decision_id / taxDecisionId: The FINAL decision to bind.
            decision_lines / decisionLines: One entry per decision line.
        """
        body = _build_bind_decision_body(params)
        resp = self._client.post(
            f"/v1/invoices/{invoice_id}/bind-tax-decision",
            json=body,
            idempotency_key=idempotency_key,
        )
        return resp.json()  # type: ignore[no-any-return]

    def finalize(
        self,
        invoice_id: str,
        payment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Finalize an invoice: assign number, lock for editing, generate legal mentions.

        Pass ``payment`` when the invoice was already collected BEFORE issuance:
        numbering and collection are applied in the SAME transaction, so the
        original PDF and Factur-X are rendered on a settled invoice and say so.
        ``payment`` is the very object :meth:`Payments.create` takes (amount in
        integer centimes), and ``paid_at`` is accepted as a snake_case alias.

        All or nothing: a collection beyond the amount due is refused
        (``422 payment_exceeds_amount_due``) and the invoice stays a draft — no
        number is burned. Without ``payment``, the behaviour is unchanged.

        Args:
            invoice_id: The draft to issue.
            payment: Optional collection received before issuance.
        """
        resp = self._client.post(
            f"/v1/invoices/{invoice_id}/finalize",
            json=_build_finalize_body(payment),
        )
        return resp.json()  # type: ignore[no-any-return]

    def email(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Send a finalized invoice to its customer by email with the PDF
        attached.

        Args:
            recipient_email / recipientEmail: override the recipient.
            custom_message / customMessage: optional body addition.
            include_xml / includeXml: attach the CII XML alongside the PDF.
            custom_subject / customSubject: override the email subject.

        Returns either ``{"status": "sent", ...}`` or, when the PDF is
        still being generated, ``{"status": "pending", "jobId": ...}`` —
        callers should poll the job id to know when delivery completes.
        """
        body = dict(params)
        for snake, camel in (
            ("recipient_email", "recipientEmail"),
            ("custom_message", "customMessage"),
            ("include_xml", "includeXml"),
            ("custom_subject", "customSubject"),
        ):
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = self._client.post(f"/v1/invoices/{invoice_id}/email", json=body)
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

    def create_portal_link(self, invoice_id: str) -> dict[str, Any]:
        """Generate a signed client-portal link for a finalized invoice.

        The URL points to a public, branded portal where the customer
        can view the invoice, download the PDF and trigger the payment
        flow. The embedded token grants read-only access to a single
        invoice and expires after the configured lifetime. Returns
        ``invalid_status_transition`` if the invoice is still in draft.
        """
        resp = self._client.post(f"/v1/invoices/{invoice_id}/portal-link")
        return resp.json()  # type: ignore[no-any-return]

    def create_incoming(self, **params: Any) -> dict[str, Any]:
        """Record a supplier invoice received outside the platform.

        Args:
            senderName: Supplier name (required).
            senderSiret: Supplier SIRET, 14 digits (required).
            amount: Total incl. VAT, in integer cents (required).
            reference: Supplier invoice number / reference (required).

        Returns:
            The recorded received-invoice dict (``rec_`` id).
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

    async def create(
        self, *, idempotency_key: str | None = None, **params: Any
    ) -> dict[str, Any]:
        """Create a draft invoice from an immutable tax decision.

        Same contract as the synchronous resource: ``taxDecisionId`` +
        ``decisionLines`` are required and ``items``/``lines`` are refused
        locally, before any HTTP call. See :meth:`Invoices.create`.
        """
        body = _build_invoice_create_body(params)
        resp = await self._client.post(
            "/v1/invoices", json=body, idempotency_key=idempotency_key
        )
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        """List invoices.

        Args:
            status: Filter by lifecycle status.
            customerId: Filter by customer ID.
            convertedFrom: Filter by source quote ID (a ``quo_…`` string);
                returns only the invoices converted from that quote.
            limit / starting_after: Pagination controls.
            **params: Any other supported query filter.
        """
        resp = await self._client.get("/v1/invoices", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Retrieve an invoice.

        Args:
            invoice_id: Invoice ID.
            expand: Comma-separated relations to inline, among
                ``customer``, ``items.product`` and ``credit_notes``. With
                ``expand="credit_notes"`` the response carries an
                ``expanded.credit_notes`` array and an ``expanded.net_balance``
                string (TTC minus issued credit notes).
            **params: Any other supported query parameter.
        """
        resp = await self._client.get(f"/v1/invoices/{invoice_id}", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        """Update a draft invoice's non-fiscal fields. See :meth:`Invoices.update`."""
        resp = await self._client.patch(f"/v1/invoices/{invoice_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, invoice_id: str) -> None:
        await self._client.delete(f"/v1/invoices/{invoice_id}")

    async def bind_tax_decision(
        self, invoice_id: str, *, idempotency_key: str | None = None, **params: Any
    ) -> dict[str, Any]:
        """Bind a FINAL tax decision to a commercial draft that already exists.

        Async twin of :meth:`Invoices.bind_tax_decision`; same contract.
        """
        body = _build_bind_decision_body(params)
        resp = await self._client.post(
            f"/v1/invoices/{invoice_id}/bind-tax-decision",
            json=body,
            idempotency_key=idempotency_key,
        )
        return resp.json()  # type: ignore[no-any-return]

    async def finalize(
        self,
        invoice_id: str,
        payment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Assign number, lock for editing, generate legal mentions.

        Async twin of :meth:`Invoices.finalize`; same contract, ``payment``
        included.
        """
        resp = await self._client.post(
            f"/v1/invoices/{invoice_id}/finalize",
            json=_build_finalize_body(payment),
        )
        return resp.json()  # type: ignore[no-any-return]

    async def email(self, invoice_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        for snake, camel in (
            ("recipient_email", "recipientEmail"),
            ("custom_message", "customMessage"),
            ("include_xml", "includeXml"),
            ("custom_subject", "customSubject"),
        ):
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/email", json=body)
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

    async def create_portal_link(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/invoices/{invoice_id}/portal-link")
        return resp.json()  # type: ignore[no-any-return]

    async def create_incoming(self, **params: Any) -> dict[str, Any]:
        """Record a supplier invoice received outside the platform.

        Args:
            senderName: Supplier name (required).
            senderSiret: Supplier SIRET, 14 digits (required).
            amount: Total incl. VAT, in integer cents (required).
            reference: Supplier invoice number / reference (required).

        Returns:
            The recorded received-invoice dict (``rec_`` id).
        """
        resp = await self._client.post("/v1/invoices/incoming", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def list_incoming(self, **params: Any) -> AsyncPage:
        """List incoming invoices."""
        resp = await self._client.get("/v1/invoices/incoming", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list_incoming, original_params=params)
