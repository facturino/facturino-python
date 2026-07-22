"""Tests for the two real gaps fixed in the Python SDK after the
post-commit audit:

  - Removed a phantom ``Payments.get(invoice_id, payment_id)`` method
    that targeted ``GET /v1/invoices/:id/payments/:id`` — the API does
    not expose that endpoint (only POST / GET-list at the collection
    level).
  - Added ``Invoices.email(invoice_id, ...)`` to match the
    ``POST /v1/invoices/:id/email`` endpoint that the other SDKs
    already exposed.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino

BASE = "https://facturino.com/api"


def test_payments_phantom_get_is_gone() -> None:
    """The phantom ``Payments.get`` method must not be reachable."""
    client = facturino.Client("fac_test_abc")
    assert not hasattr(client.payments, "get"), (
        "Payments.get() targeted a non-existent endpoint and was removed."
    )


@respx.mock
def test_payments_cancel_posts_to_cancel_endpoint() -> None:
    route = respx.post(f"{BASE}/v1/invoices/inv_x/payments/pay_x/cancel").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "pay_x",
                "object": "payment",
                "status": "cancelled",
                "invoiceStatus": "partially_paid",
                "amountDue": 5000,
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.payments.cancel("inv_x", "pay_x")

    assert result["status"] == "cancelled"
    assert result["amountDue"] == 5000
    assert route.called


@respx.mock
def test_credit_notes_refund_posts_to_refund_endpoint() -> None:
    route = respx.post(f"{BASE}/v1/credit-notes/crn_1/refund").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "ref_1",
                "object": "refund",
                "creditNoteId": "crn_1",
                "invoiceId": "inv_1",
                "amount": 12000,
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.credit_notes.refund("crn_1", amount=12000, method="transfer", refunded_at="2026-05-14")

    assert result["object"] == "refund"
    assert result["amount"] == 12000
    # Snake-case refunded_at is serialised to camelCase refundedAt in the body.
    body = route.calls.last.request.content.decode()
    assert "refundedAt" in body
    assert route.called


@respx.mock
def test_invoices_email_sends_camel_case_body() -> None:
    route = respx.post(f"{BASE}/v1/invoices/inv_x/email").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "sent",
                "invoiceId": "inv_x",
                "recipient": "buyer@example.com",
                "sentAt": "2026-05-20T12:00:00Z",
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.invoices.email(
        "inv_x",
        recipient_email="buyer@example.com",
        custom_message="Merci",
        include_xml=True,
        custom_subject="Votre facture",
    )

    assert result["status"] == "sent"
    body = route.calls.last.request.read().decode()
    # snake_case -> camelCase mapping
    assert "recipientEmail" in body and "buyer@example.com" in body
    assert "customMessage" in body and "Merci" in body
    assert "includeXml" in body
    assert "customSubject" in body
    # And the snake_case form must NOT leak onto the wire
    assert "recipient_email" not in body
    assert "include_xml" not in body


@respx.mock
def test_invoices_email_handles_pending_pdf_response() -> None:
    """When the PDF is still rendering the API returns a job handle."""
    respx.post(f"{BASE}/v1/invoices/inv_y/email").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "pending",
                "invoiceId": "inv_y",
                "jobId": "job_pdf_123",
                "pollUrl": "/v1/jobs/job_pdf_123",
                "reason": "pdf_generating",
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.invoices.email("inv_y")

    assert result["status"] == "pending"
    assert result["jobId"] == "job_pdf_123"


@respx.mock
@pytest.mark.asyncio
async def test_async_invoices_email() -> None:
    respx.post(f"{BASE}/v1/invoices/inv_x/email").mock(
        return_value=httpx.Response(200, json={"status": "sent", "invoiceId": "inv_x"})
    )

    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.invoices.email("inv_x", recipient_email="b@x.com")
    assert result["status"] == "sent"


def test_async_payments_phantom_get_is_gone() -> None:
    async_client = facturino.AsyncClient("fac_test_abc")
    assert not hasattr(async_client.payments, "get")


@respx.mock
def test_archives_namespace_is_wired() -> None:
    """The ``archives`` resource is exported and must be reachable on the client."""
    respx.get(f"{BASE}/v1/archives/inv_x").mock(
        return_value=httpx.Response(200, json={"id": "inv_x", "archive": {"hash": "abc"}})
    )

    client = facturino.Client("fac_test_abc")
    assert hasattr(client, "archives")
    assert client.archives.get("inv_x")["archive"]["hash"] == "abc"


@respx.mock
@pytest.mark.asyncio
async def test_async_archives_namespace_is_wired() -> None:
    respx.get(f"{BASE}/v1/archives/inv_x").mock(
        return_value=httpx.Response(200, json={"id": "inv_x", "archive": {"hash": "abc"}})
    )

    async with facturino.AsyncClient("fac_test_abc") as client:
        assert hasattr(client, "archives")
        entry = await client.archives.get("inv_x")
    assert entry["archive"]["hash"] == "abc"
