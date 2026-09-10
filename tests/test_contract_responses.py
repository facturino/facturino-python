"""The exact local server responses are shared by all four SDKs."""

import json
from pathlib import Path
from typing import get_type_hints

import pytest
import respx

import facturino
from facturino import _types
from facturino.event_data import EVENT_DATA_TYPES

RESOURCES = {
    "invoice": "Invoice",
    "payment": "Payment",
    "customer": "Customer",
    "creditNote": "CreditNote",
    "taxDecision": "TaxDecision",
    "event": "WebhookEvent",
}


def fixture(name):
    return json.loads((Path(__file__).parent / "fixtures/contract" / f"{name}.json").read_text())


@pytest.mark.parametrize("name", RESOURCES)
@respx.mock
def test_actual_resource_response(name):
    body = fixture(name)
    respx.route().respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        calls = {
            "invoice": lambda: client.invoices.get(body["id"]),
            "payment": lambda: client.payments.create(
                body["invoiceId"], amount=50000, method="transfer", paid_at=body["paidAt"]
            ),
            "customer": lambda: client.customers.get(body["id"]),
            "creditNote": lambda: client.credit_notes.get(body["id"]),
            "taxDecision": lambda: client.tax_decisions.get(body["id"]),
            "event": lambda: client.events.get(body["id"]),
        }
        assert calls[name]() == body
    assert set(body) <= set(get_type_hints(getattr(_types, RESOURCES[name])))


def test_every_example_has_a_payload_projection_without_losing_null_or_missing_keys():
    for event in fixture("events"):
        fields = get_type_hints(EVENT_DATA_TYPES[event["type"]])
        assert set(event["data"]) <= set(fields)
    assert fixture("payment")["recorded_by"] == "api"
    assert "recordedBy" not in fixture("payment")
    assert "fr212" not in fixture("payment")
    assert fixture("invoice")["archive"] is None
