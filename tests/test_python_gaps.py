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
