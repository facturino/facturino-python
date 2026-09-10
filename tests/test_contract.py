"""Contract reads are exercised through mocked HTTP and signed local payloads."""

import hashlib
import hmac
import json
import time
from pathlib import Path
from typing import get_args, get_type_hints

import pytest
import respx

import facturino
from facturino._types import (
    InvoiceEinvoicing,
    PaRejectionCategory,
    PaRejectionSource,
    PaymentCollectionStatus,
    WebhookEvent,
)

FIXTURE = json.loads((Path(__file__).parent / "fixtures/contract-2.7.0.json").read_text())
BASE = "https://facturino.com/api"


def test_enums_and_nullable_models():
    assert len(get_args(PaRejectionCategory)) == 11
    assert {"addressing_error", "other"} <= set(get_args(PaRejectionCategory))
    assert set(get_args(PaRejectionSource)) == {"platform", "buyer", "facturino"}
    assert type(None) in get_args(get_type_hints(InvoiceEinvoicing)["rejectionSource"])
    assert type(None) in get_args(get_type_hints(PaymentCollectionStatus)["sentAt"])
    assert "data" in get_type_hints(WebhookEvent)


@respx.mock
def test_invoice_resource_preserves_rejection_and_archive():
    respx.get(f"{BASE}/v1/invoices/inv_00090").respond(json=FIXTURE["invoice"])
    result = facturino.Client("fac_test_contract").invoices.get("inv_00090")
    assert result == FIXTURE["invoice"]
    assert result["einvoicing"]["rejectionCategory"] == "addressing_error"
    assert (
        result["einvoicing"]["previousSubmissions"][0]["rejectionNote"] == "L’adresse de réception doit être confirmée."
    )


def test_signed_events_preserve_nulls():
    secret = "whsec_contract_fixture"
    timestamp = int(time.time())
    for event in FIXTURE["events"]:
        payload = json.dumps(event)
        signature = hmac.new(secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256).hexdigest()
        assert facturino.Webhook.construct_event(payload, f"t={timestamp},v1={signature}", secret) == event


@respx.mock
def test_retry_returns_receipt_for_targeted_replay():
    receipt = {"id": "evt_example", "object": "event", "retryScheduled": True, "endpointId": "we_example"}
    route = respx.post(f"{BASE}/v1/events/evt_example/retry").respond(json=receipt)
    assert facturino.Client("fac_test_contract").events.retry("evt_example", endpoint_id="we_example") == receipt
    assert json.loads(route.calls.last.request.content) == {"endpointId": "we_example"}


@pytest.mark.asyncio
@respx.mock
async def test_async_retry_returns_the_same_receipt():
    receipt = {"id": "evt_example", "object": "event", "retryScheduled": True, "endpointId": "we_example"}
    route = respx.post(f"{BASE}/v1/events/evt_example/retry").respond(json=receipt)
    async with facturino.AsyncClient("fac_test_contract") as client:
        assert await client.events.retry("evt_example", endpoint_id="we_example") == receipt
    assert json.loads(route.calls.last.request.content) == {"endpointId": "we_example"}


def test_other_response_facts():
    assert FIXTURE["payment"]["fr212"]["state"] == "awaiting_deposit"
    assert FIXTURE["blockedPayment"]["fr212"]["lastErrorReason"] == "Invoice identifier is rejected."
    assert FIXTURE["creditNote"]["relatedInvoiceNumber"] == "FAC2026-00090"
    assert FIXTURE["customer"]["warnings"][0]["code"] == "buyer_nature_suspect"
    assert FIXTURE["taxDecision"]["warnings"][0]["param"] == "customerId"
