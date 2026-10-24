"""SDK-only contract cases; shared server-response corpus stays unchanged."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, get_type_hints

import pytest
import respx

import facturino
from facturino import _types
from facturino._client import DEFAULT_BASE_URL

BASE = DEFAULT_BASE_URL
CLASSIFICATIONS = [
    ("goods", "goods"),
    ("service", "services"),
    ("service", "electronically_supplied_services"),
    ("service", "deposit"),
    ("goods", "ancillary_costs"),
    ("service", "future_supply_category"),
    ("service", None),
    (None, "services"),
    (None, None),
]


def fixture(name):
    path = Path(__file__).parent / "fixtures/supply-categories.json"
    return json.loads(path.read_text())[name]


def classification(kind, category):
    fields = {}
    if kind is not None:
        fields["kind"] = kind
    if category is not None:
        fields["supplyCategory"] = category
    return fields


def test_product_quote_and_decision_types_match_the_additive_contract():
    for model in (_types.Product, _types.ProductCreateParams, _types.ProductUpdateParams, _types.LineItem):
        fields = get_type_hints(model)
        assert fields["kind"] == Literal["goods", "service"]
        assert fields["supplyCategory"] is str
        assert {"kind", "supplyCategory"} <= model.__optional_keys__
    for model in (_types.Product, _types.ProductCreateParams, _types.ProductUpdateParams):
        fields = get_type_hints(model)
        assert fields["vatexCode"] is str
        assert fields["tags"] == list[str]
        assert set(fixture("product")) <= set(get_type_hints(_types.Product))
    update = get_type_hints(_types.ProductUpdateParams)
    assert update["reference"] is str
    assert update["category"] is str
    assert update["active"] is bool
    assert update["vatCode"] is str
    assert facturino.Product is _types.Product
    assert get_type_hints(_types.QuoteCreateParams)["items"] == list[_types.LineItem]
    assert get_type_hints(_types.QuoteUpdateParams)["lines"] == list[_types.LineItem]
    assert get_type_hints(_types.TaxDecisionLine)["category"] == str | None
    assert get_type_hints(_types.TaxDecisionLineInput)["category"] is str
    assert _types.TaxDecisionLineInput.__required_keys__ == {"category"}
    assert get_type_hints(_types.TaxDecisionIssue)["code"] is str
    assert get_type_hints(_types.TaxDecisionNotice)["code"] is str


def product_case(kind, category):
    body = fixture("product")
    body.pop("kind")
    body.pop("supplyCategory")
    body.update(classification(kind, category))
    params = {key: value for key, value in body.items() if key not in ("id", "object", "active", "livemode", "created")}
    patch = {**params, "reference": "COURSE-2", "category": "training", "active": False}
    updated = {**body, "reference": "COURSE-2", "active": False}
    create = respx.post(f"{BASE}/v1/products").respond(201, json=body)
    update = respx.patch(f"{BASE}/v1/products/{body['id']}").respond(json=updated)
    respx.get(f"{BASE}/v1/products/{body['id']}").respond(json=updated)
    return body, params, patch, updated, create, update


@pytest.mark.parametrize(("kind", "category"), CLASSIFICATIONS)
@respx.mock
def test_product_fields_serialize_and_round_trip_without_defaults(kind, category):
    body, params, patch, updated, create, update = product_case(kind, category)
    with facturino.Client("fac_test_supply_category") as client:
        assert client.products.create(**params) == body
        assert client.products.update(body["id"], **patch) == updated
        assert client.products.get(body["id"]) == updated
    assert json.loads(create.calls.last.request.content) == params
    assert json.loads(update.calls.last.request.content) == patch


@pytest.mark.parametrize(("kind", "category"), CLASSIFICATIONS)
@respx.mock
async def test_async_product_fields_serialize_and_round_trip_without_defaults(kind, category):
    body, params, patch, updated, create, update = product_case(kind, category)
    async with facturino.AsyncClient("fac_test_supply_category") as client:
        assert await client.products.create(**params) == body
        assert await client.products.update(body["id"], **patch) == updated
        assert await client.products.get(body["id"]) == updated
    assert json.loads(create.calls.last.request.content) == params
    assert json.loads(update.calls.last.request.content) == patch


def quote_case(kind, category):
    quote, invoice = fixture("quote"), fixture("convertedInvoice")
    for line in (quote["items"][0], invoice["commercialDraft"]["lines"][0]):
        line.pop("kind")
        line.pop("supplyCategory")
        line.update(classification(kind, category))
    create = respx.post(f"{BASE}/v1/quotes").respond(201, json=quote)
    update = respx.patch(f"{BASE}/v1/quotes/{quote['id']}").respond(json=quote)
    respx.get(f"{BASE}/v1/quotes/{quote['id']}").respond(json=quote)
    convert = respx.post(f"{BASE}/v1/quotes/{quote['id']}/convert").respond(201, json=invoice)
    return quote, invoice, create, update, convert


@pytest.mark.parametrize(("kind", "category"), CLASSIFICATIONS)
@respx.mock
def test_quote_line_fields_survive_create_update_read_and_conversion(kind, category):
    quote, invoice, create, update, convert = quote_case(kind, category)
    with facturino.Client("fac_test_supply_category") as client:
        assert client.quotes.create(customer="cus_1", items=quote["items"]) == quote
        assert client.quotes.update(quote["id"], lines=quote["items"]) == quote
        assert client.quotes.get(quote["id"]) == quote
        assert client.quotes.convert(quote["id"]) == invoice
    assert json.loads(create.calls.last.request.content) == {"customerId": "cus_1", "lines": quote["items"]}
    assert json.loads(update.calls.last.request.content) == {"lines": quote["items"]}
    assert invoice["commercialDraft"]["lines"] == quote["items"]
    assert convert.call_count == 1


@pytest.mark.parametrize(("kind", "category"), CLASSIFICATIONS)
@respx.mock
async def test_async_quote_line_fields_survive_create_update_read_and_conversion(kind, category):
    quote, invoice, create, update, convert = quote_case(kind, category)
    async with facturino.AsyncClient("fac_test_supply_category") as client:
        assert await client.quotes.create(customer="cus_1", items=quote["items"]) == quote
        assert await client.quotes.update(quote["id"], lines=quote["items"]) == quote
        assert await client.quotes.get(quote["id"]) == quote
        assert await client.quotes.convert(quote["id"]) == invoice
    assert json.loads(create.calls.last.request.content) == {"customerId": "cus_1", "lines": quote["items"]}
    assert json.loads(update.calls.last.request.content) == {"lines": quote["items"]}
    assert invoice["commercialDraft"]["lines"] == quote["items"]
    assert convert.call_count == 1


def decision_case(state):
    body = fixture("pendingDecision" if state == "pending" else "finalDecision")
    if state == "historical":
        body["notices"] = []
    respx.get(f"{BASE}/v1/tax-decisions/{body['id']}").respond(json=body)
    return body


@pytest.mark.parametrize("state", ["pending", "final", "historical"])
@respx.mock
def test_undeclared_category_responses_preserve_null_and_historical_values(state):
    body = decision_case(state)
    with facturino.Client("fac_test_supply_category") as client:
        decision = client.tax_decisions.get(body["id"])
    assert decision == body
    assert_decision_category(decision, state)


@pytest.mark.parametrize("state", ["pending", "final", "historical"])
@respx.mock
async def test_async_undeclared_category_responses_preserve_null_and_historical_values(state):
    body = decision_case(state)
    async with facturino.AsyncClient("fac_test_supply_category") as client:
        decision = await client.tax_decisions.get(body["id"])
    assert decision == body
    assert_decision_category(decision, state)


def assert_decision_category(decision, state):
    line = decision["lines"][0]
    if state == "pending":
        assert decision["status"] == "pending_verification"
        assert line["category"] is None
        assert decision["totals"] is None
        assert decision["amountToCharge"] is None
        assert not {"amountHT", "amountVAT", "amountTTC"} & line.keys()
        assert decision["issues"][0]["code"] == "supply_category_not_declared"
        assert decision["notices"] == []
    else:
        assert decision["status"] == "final"
        assert line["category"] == "services"
        assert decision["amountToCharge"] == 12000
        assert decision["issues"] == []
        assert decision["notices"] == ([] if state == "historical" else fixture("finalDecision")["notices"])
    assert "supplyCategory" not in line


@pytest.mark.parametrize("tax_source", ["facturino", "integration"])
@respx.mock
def test_direct_tax_decision_creation_still_sends_an_explicit_category(tax_source):
    body = fixture("finalDecision")
    body["notices"] = []
    route = respx.post(f"{BASE}/v1/tax-decisions").respond(201, json=body)
    line = direct_line(tax_source)
    with facturino.Client("fac_test_supply_category") as client:
        client.tax_decisions.create(
            tax_source=tax_source, customer_id="cus_1", effective_at="2026-10-24",
            currency="eur", price_mode="tax_exclusive", lines=[line], idempotency_key="declared-category",
        )
    assert json.loads(route.calls.last.request.content)["lines"][0]["category"] == "services"


@pytest.mark.parametrize("tax_source", ["facturino", "integration"])
@respx.mock
async def test_async_direct_tax_decision_creation_still_sends_an_explicit_category(tax_source):
    body = fixture("finalDecision")
    body["notices"] = []
    route = respx.post(f"{BASE}/v1/tax-decisions").respond(201, json=body)
    line = direct_line(tax_source)
    async with facturino.AsyncClient("fac_test_supply_category") as client:
        await client.tax_decisions.create(
            tax_source=tax_source, customer_id="cus_1", effective_at="2026-10-24",
            currency="eur", price_mode="tax_exclusive", lines=[line], idempotency_key="declared-category",
        )
    assert json.loads(route.calls.last.request.content)["lines"][0]["category"] == "services"


def direct_line(tax_source):
    line = {
        "reference": "line-1", "description": "Declared service", "category": "services",
        "rateCategory": "standard", "unitAmount": 10000, "quantity": "1",
    }
    if tax_source == "integration":
        line.update(vatRate=2000, vatCode="S")
    return line
