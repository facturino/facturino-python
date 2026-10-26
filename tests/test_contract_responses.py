"""Shared local server responses and SDK-only compatible response fixtures."""

import json
from pathlib import Path
from typing import Any, Literal, get_type_hints

import httpx
import pytest
import respx

import facturino
from facturino import _types
from facturino._client import DEFAULT_BASE_URL
from facturino.event_data import EVENT_DATA_TYPES

RESOURCES = {
    "invoice": "Invoice",
    "payment": "Payment",
    "customer": "Customer",
    "creditNote": "CreditNote",
    "taxDecision": "TaxDecision",
    "legal-category": "TaxDecision",
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
            "legal-category": lambda: client.tax_decisions.get(body["id"]),
            "event": lambda: client.events.get(body["id"]),
        }
        assert calls[name]() == body
    assert set(body) <= set(get_type_hints(getattr(_types, RESOURCES[name])))


NOTICE = {
    "code": "vat_number_territory_mismatch",
    "detailCode": "vat_number_ignored_national_registration",
    "message": "The VAT number was set aside: the national registration establishes the business status.",
    "reference": "Implementing Regulation (EU) 282/2011 art. 18",
    "lineId": "line-1",
}
BARE_NOTICE = {
    "code": "destination_mechanism_missing",
    "message": "Destination VAT is invoiced; register through the Union scheme or locally.",
}
ISSUE = {
    "code": "business_status_not_evidenced",
    "detailCode": "einvoicing_buyer_registration_required",
    "message": "The buyer SIRET is required for the electronic invoice.",
    "reference": "CGI art. 242 nonies A",
    "lineId": "line-1",
}


def decision_with(customer, **fields):
    body = fixture("taxDecision")
    body["customer"] = {**body["customer"], **customer}
    return {**body, **fields}


def test_the_corpus_carries_frozen_decision_fields():
    decision = fixture("taxDecision")
    assert decision["notices"] == []
    assert decision["customer"]["retainedVatNumber"] is None
    assert decision["obligationBasis"] == "legal"
    # The shared invoice is bound to a historical decision: the basis is omitted, not null.
    assert "obligationBasis" not in fixture("invoice")["taxSnapshot"]
    assert fixture("invoice")["taxSnapshot"]["notices"] == []
    assert fixture("creditNote")["taxSnapshot"]["notices"] == []


def test_reporting_obligation_fields_are_optional_nullable_and_exported():
    for model in (_types.EReporting, _types.TaxDecision, _types.TaxSnapshot):
        hints = get_type_hints(model)
        assert hints["obligationBasis"] == Literal["legal", "voluntary_early_adoption"] | None
        assert "obligationBasis" in model.__optional_keys__
    reporting = get_type_hints(_types.EReporting)
    assert reporting["obligationDueFrom"] == str | None
    assert reporting["acknowledgedBy"] == Literal["administration", "platform"] | None
    assert {"obligationDueFrom", "acknowledgedBy"} <= _types.EReporting.__optional_keys__
    for model in (_types.EReporting, _types.TaxSnapshot):
        assert getattr(facturino, model.__name__) is model
        assert model.__name__ in facturino.__all__
    snapshot = get_type_hints(_types.TaxSnapshot)
    for name, model in (("invoice", _types.Invoice), ("creditNote", _types.CreditNote)):
        assert set(fixture(name)["taxSnapshot"]) <= set(snapshot)
        assert get_type_hints(model)["taxSnapshot"] == dict[str, Any]


REPORTING_OBLIGATION_FIELDS = [
    pytest.param({
        "obligationBasis": "legal", "obligationDueFrom": "2026-09-01", "acknowledgedBy": "administration",
    }, id="legal"),
    pytest.param({
        "obligationBasis": "voluntary_early_adoption", "obligationDueFrom": "2027-09-01", "acknowledgedBy": "platform",
    }, id="voluntary"),
    pytest.param({
        "obligationBasis": None, "obligationDueFrom": None, "acknowledgedBy": None,
    }, id="null"),
    pytest.param({}, id="historical"),
]


def reporting_declaration_with(fields):
    return {
        "id": "erep_fixture", "object": "ereporting", "status": "submitted",
        "type": "b2c", "period": "2026-10", **fields,
    }


@pytest.mark.parametrize("fields", REPORTING_OBLIGATION_FIELDS)
@respx.mock
def test_declaration_preserves_reporting_obligation_fields(fields):
    body = reporting_declaration_with(fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/ereporting/declarations/{body['id']}").respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        assert client.ereporting.get(body["id"]) == body
    assert set(body) <= set(get_type_hints(_types.EReporting))


@pytest.mark.parametrize("fields", REPORTING_OBLIGATION_FIELDS)
@respx.mock
async def test_async_declaration_preserves_reporting_obligation_fields(fields):
    body = reporting_declaration_with(fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/ereporting/declarations/{body['id']}").respond(json=body)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        assert await client.ereporting.get(body["id"]) == body


def test_reporting_skipped_reason_is_optional_nullable_and_open():
    hints = get_type_hints(_types.EReporting)
    assert hints["state"] is str
    assert hints["skippedReason"] == str | None
    assert "skippedReason" in _types.EReporting.__optional_keys__
    assert "skippedReason" not in get_type_hints(_types.EreportingCreateParams)


REPORTING_SKIPPED_FIELDS = [
    pytest.param({
        "status": "skipped", "state": "skipped", "skippedReason": "nothing_to_declare",
        "type": "payment_international",
        "obligation": {
            "state": "completed", "reasonCode": None, "reasonSource": None,
            "owner": None, "action": None, "nextAttemptAt": None,
        },
    }, id="nothing-to-declare"),
    pytest.param({"state": "reserved", "skippedReason": None}, id="null"),
    pytest.param({"status": "skipped", "state": "blocked"}, id="historical"),
    pytest.param({"state": "future_state", "skippedReason": "future_reason"}, id="future"),
]


@pytest.mark.parametrize("fields", REPORTING_SKIPPED_FIELDS)
@respx.mock
def test_declaration_preserves_skipped_reason(fields):
    body = reporting_declaration_with(fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/ereporting/declarations/{body['id']}").respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        assert client.ereporting.get(body["id"]) == body
    assert set(body) <= set(get_type_hints(_types.EReporting))


@pytest.mark.parametrize("fields", REPORTING_SKIPPED_FIELDS)
@respx.mock
async def test_async_declaration_preserves_skipped_reason(fields):
    body = reporting_declaration_with(fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/ereporting/declarations/{body['id']}").respond(json=body)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        assert await client.ereporting.get(body["id"]) == body


OBLIGATION_BASIS_FIELDS = [
    pytest.param({"obligationBasis": "legal"}, id="legal"),
    pytest.param({"obligationBasis": "voluntary_early_adoption"}, id="voluntary"),
    pytest.param({"obligationBasis": None}, id="null"),
    pytest.param({}, id="historical"),
]


def resource_with_obligation_basis(name, fields):
    body = fixture(name)
    position = body if name == "taxDecision" else body["taxSnapshot"]
    position.pop("obligationBasis", None)
    position.update(fields)
    return body


@pytest.mark.parametrize("name,resource,path", [
    ("taxDecision", "tax_decisions", "tax-decisions"),
    ("invoice", "invoices", "invoices"),
    ("creditNote", "credit_notes", "credit-notes"),
])
@pytest.mark.parametrize("fields", OBLIGATION_BASIS_FIELDS)
@respx.mock
def test_decision_and_snapshot_preserve_obligation_basis(name, resource, path, fields):
    body = resource_with_obligation_basis(name, fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/{path}/{body['id']}").respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        assert getattr(client, resource).get(body["id"]) == body


@pytest.mark.parametrize("name,resource,path", [
    ("taxDecision", "tax_decisions", "tax-decisions"),
    ("invoice", "invoices", "invoices"),
    ("creditNote", "credit_notes", "credit-notes"),
])
@pytest.mark.parametrize("fields", OBLIGATION_BASIS_FIELDS)
@respx.mock
async def test_async_decision_and_snapshot_preserve_obligation_basis(name, resource, path, fields):
    body = resource_with_obligation_basis(name, fields)
    respx.get(f"{DEFAULT_BASE_URL}/v1/{path}/{body['id']}").respond(json=body)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        assert await getattr(client, resource).get(body["id"]) == body


def test_legal_category_is_optional_exported_and_preserves_open_strings():
    hints = get_type_hints(_types.TaxDecision)
    assert hints["legalCategory"] is _types.TaxDecisionLegalCategory
    assert "legalCategory" in _types.TaxDecision.__optional_keys__
    assert "legalCategory" not in fixture("taxDecision")
    assert facturino.TaxDecisionLegalCategory is _types.TaxDecisionLegalCategory
    assert "TaxDecisionLegalCategory" in facturino.__all__
    category = get_type_hints(_types.TaxDecisionLegalCategory)
    assert set(category) == set(fixture("legal-category")["legalCategory"])
    assert category == {
        "source": Literal["sirene"], "siren": str, "status": str,
        "legalCategoryCode": str | None, "checkedAt": str,
    }
    for model in (_types.TaxDecisionNotice, _types.TaxDecisionIssue):
        fields = get_type_hints(model)
        assert fields["code"] is str
        assert fields["detailCode"] is str


def assert_legal_category_response(decision, status, code):
    category = decision["legalCategory"]
    assert category["source"] == "sirene"
    assert category["siren"] == "123456789"
    assert category["status"] == status
    assert category["legalCategoryCode"] == code
    assert category["checkedAt"] == "2026-09-15"


def legal_category_body(status, code):
    body = fixture("legal-category")
    body["legalCategory"].update(status=status, legalCategoryCode=code)
    if status in ("not_found", "unavailable"):
        body.update(
            status="pending_verification", totals=None, amountToCharge=None,
            issues=[{
                "code": "business_status_not_evidenced",
                "detailCode": "legal_category_unresolved",
                "message": "SIRENE could not give the legal category; supply the buyer's tax status.",
            }],
        )
    return body


@pytest.mark.parametrize("status,code", [
    ("found", "5499"), ("not_found", None), ("unavailable", None), ("future_status", "future_code"),
])
@respx.mock
def test_legal_category_fixture_round_trips_every_field(status, code):
    body = legal_category_body(status, code)
    respx.get(f"{DEFAULT_BASE_URL}/v1/tax-decisions/{body['id']}").respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        decision = client.tax_decisions.get(body["id"])
    assert decision == body
    assert_legal_category_response(decision, status, code)


@pytest.mark.parametrize("status,code", [
    ("found", "5499"), ("not_found", None), ("unavailable", None), ("future_status", "future_code"),
])
@respx.mock
async def test_async_legal_category_fixture_round_trips_every_field(status, code):
    body = legal_category_body(status, code)
    respx.get(f"{DEFAULT_BASE_URL}/v1/tax-decisions/{body['id']}").respond(json=body)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        decision = await client.tax_decisions.get(body["id"])
    assert decision == body
    assert_legal_category_response(decision, status, code)


def test_notices_and_issue_details_are_typed():
    hints = get_type_hints(_types.TaxDecision)
    assert hints["notices"] == list[_types.TaxDecisionNotice]
    # Kept as plain dicts so code typed against the earlier annotation still checks.
    assert hints["issues"] == list[dict[str, Any]]
    assert set(NOTICE) <= set(get_type_hints(_types.TaxDecisionNotice))
    assert set(ISSUE) <= set(get_type_hints(_types.TaxDecisionIssue))
    assert facturino.TaxDecisionNotice is _types.TaxDecisionNotice
    assert facturino.TaxDecisionIssue is _types.TaxDecisionIssue


@respx.mock
def test_a_final_decision_hydrates_its_notices_and_the_retained_vat_number():
    kept = decision_with(
        {"natureBasis": "declared_business_with_valid_vat_number", "vatNumber": "DE811128135",
         "retainedVatNumber": "DE811128135"},
        notices=[NOTICE, BARE_NOTICE],
    )
    unevidenced = decision_with(
        {"nature": "consumer", "natureBasis": "declared_business_not_evidenced",
         "vatNumber": None, "retainedVatNumber": None},
        notices=[{"code": "business_status_not_evidenced",
                  "message": "No VAT number communicated: electronic services follow art. 18(2)."}],
    )
    unevidenced["lines"][0]["category"] = "electronically_supplied_services"
    unevidenced["lines"][0]["effectiveCategory"] = "electronically_supplied_services"
    respx.route().mock(side_effect=[httpx.Response(200, json=kept), httpx.Response(200, json=unevidenced)])
    with facturino.Client("fac_test_corpus") as client:
        decision = client.tax_decisions.get("taxdec_c6_fixture")
        assert decision["status"] == "final"
        assert decision["notices"] == [NOTICE, BARE_NOTICE]
        assert decision["notices"][0]["detailCode"] == "vat_number_ignored_national_registration"
        assert "detailCode" not in decision["notices"][1]
        assert decision["customer"]["retainedVatNumber"] == "DE811128135"
        for notice in decision["notices"]:
            assert set(notice) <= set(get_type_hints(_types.TaxDecisionNotice))

        # Art. 18(2): electronic services, EU VAT territory, no number communicated.
        decision = client.tax_decisions.get("taxdec_c6_fixture")
        assert decision["customer"]["natureBasis"] == "declared_business_not_evidenced"
        assert decision["customer"]["vatNumber"] is None
        assert decision["customer"]["retainedVatNumber"] is None


@respx.mock
def test_a_pending_decision_hydrates_the_issue_detail():
    pending = decision_with(
        {}, status="pending_verification", totals=None, amountToCharge=None,
        issues=[ISSUE, {"code": "vies_unavailable", "message": "VIES is unreachable."}],
    )
    respx.route().respond(json=pending)
    with facturino.Client("fac_test_corpus") as client:
        decision = client.tax_decisions.get("taxdec_c6_fixture")
    assert decision["issues"][0] == ISSUE
    assert decision["issues"][0]["detailCode"] == "einvoicing_buyer_registration_required"
    assert "detailCode" not in decision["issues"][1]
    for issue in decision["issues"]:
        assert set(issue) <= set(get_type_hints(_types.TaxDecisionIssue))


@respx.mock
def test_documents_hydrate_the_notices_frozen_with_their_decision():
    invoice = fixture("invoice")
    invoice["taxSnapshot"]["notices"] = [NOTICE, BARE_NOTICE]
    credit_note = fixture("creditNote")
    credit_note["taxSnapshot"]["notices"] = [NOTICE]
    respx.route().mock(side_effect=[httpx.Response(200, json=invoice), httpx.Response(200, json=credit_note)])
    with facturino.Client("fac_test_corpus") as client:
        assert client.invoices.get("inv_c6_fixture")["taxSnapshot"]["notices"] == [NOTICE, BARE_NOTICE]
        assert client.credit_notes.get("crn_c6_fixture")["taxSnapshot"]["notices"] == [NOTICE]


def test_every_example_has_a_payload_projection_without_losing_null_or_missing_keys():
    for event in fixture("events"):
        fields = get_type_hints(EVENT_DATA_TYPES[event["type"]])
        assert set(event["data"]) <= set(fields)
    assert fixture("payment")["recorded_by"] == "api"
    assert "recordedBy" not in fixture("payment")
    assert "fr212" not in fixture("payment")
    assert fixture("invoice")["archive"] is None


LOCAL_TAX = {
    "code": "tgca_mf",
    "rateCentipercent": 400,
    "amount": 400,
    "reference": "CGISM",
    "exemption": None,
}
LOCAL_TAX_REGISTRATION = {
    "territory": "MF",
    "reference": "TGCA-REG-1",
    "effectiveFrom": "2026-09-01",
    "effectiveTo": None,
}


def test_local_tax_shapes_are_optional_and_strings_stay_open():
    for model in (_types.CustomerCreateParams, _types.CustomerUpdateParams, _types.Customer):
        assert get_type_hints(model)["taxStatus"] == Literal["taxable", "non_taxable"]
        assert "taxStatus" in model.__optional_keys__

    for model in (
        _types.LocalTax, _types.LocalTaxRegistration, _types.TaxDecisionSellerProfile,
        _types.TaxDecisionLine, _types.TaxDecisionTotals,
    ):
        assert not model.__required_keys__
    for name in (
        "LocalTax", "LocalTaxRegistration", "TaxDecisionSellerProfile", "TaxDecisionLine", "TaxDecisionTotals",
    ):
        assert getattr(facturino, name) is getattr(_types, name)

    tax = get_type_hints(_types.LocalTax)
    assert set(tax) == set(LOCAL_TAX)
    assert tax["code"] is str
    assert tax["exemption"] == str | None
    assert tax["rateCentipercent"] is int
    assert tax["amount"] is int
    registration = get_type_hints(_types.LocalTaxRegistration)
    assert set(registration) == set(LOCAL_TAX_REGISTRATION)
    assert registration["territory"] is str
    assert registration["effectiveFrom"] is str
    assert registration["effectiveTo"] == str | None
    assert get_type_hints(_types.TaxDecisionLineInput)["localTaxExemption"] is str
    assert get_type_hints(_types.LineItem)["localTax"] is _types.LocalTax
    assert get_type_hints(_types.TaxDecisionLine)["localTax"] is _types.LocalTax
    assert get_type_hints(_types.TaxDecisionSellerProfile)["localTaxRegistrations"] == list[_types.LocalTaxRegistration]
    for model in (_types.Totals, _types.TaxDecisionTotals):
        assert get_type_hints(model)["totalLocalTax"] is int
        assert "totalLocalTax" in model.__optional_keys__

    # Supplemental shapes keep the existing broad annotations compatible.
    decision = get_type_hints(_types.TaxDecision)
    assert decision["sellerProfile"] == dict[str, Any]
    assert decision["lines"] == list[dict[str, Any]]
    assert decision["totals"] == dict[str, Any] | None
    corpus = fixture("taxDecision")
    for value, model in (
        (corpus["sellerProfile"], _types.TaxDecisionSellerProfile),
        (corpus["lines"][0], _types.TaxDecisionLine),
        (corpus["totals"], _types.TaxDecisionTotals),
    ):
        assert set(value) <= set(get_type_hints(model))


@pytest.mark.parametrize("tax_status", [None, "taxable", "non_taxable"])
@respx.mock
def test_customer_tax_status_round_trips_on_create_update_and_read(tax_status):
    body = fixture("customer")
    params = {} if tax_status is None else {"taxStatus": tax_status}
    body.update(params)
    create = respx.post(f"{DEFAULT_BASE_URL}/v1/customers").respond(201, json=body)
    update = respx.patch(f"{DEFAULT_BASE_URL}/v1/customers/{body['id']}").respond(json=body)
    respx.get(f"{DEFAULT_BASE_URL}/v1/customers/{body['id']}").respond(json=body)
    with facturino.Client("fac_test_corpus") as client:
        assert client.customers.create(name=body["name"], **params) == body
        assert client.customers.update(body["id"], **params) == body
        assert client.customers.get(body["id"]) == body
    assert json.loads(create.calls.last.request.content) == {"name": body["name"], **params}
    assert json.loads(update.calls.last.request.content) == params


@pytest.mark.parametrize("tax_status", [None, "taxable", "non_taxable"])
@respx.mock
async def test_async_customer_tax_status_round_trips_on_create_update_and_read(tax_status):
    body = fixture("customer")
    params = {} if tax_status is None else {"taxStatus": tax_status}
    body.update(params)
    create = respx.post(f"{DEFAULT_BASE_URL}/v1/customers").respond(201, json=body)
    update = respx.patch(f"{DEFAULT_BASE_URL}/v1/customers/{body['id']}").respond(json=body)
    respx.get(f"{DEFAULT_BASE_URL}/v1/customers/{body['id']}").respond(json=body)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        assert await client.customers.create(name=body["name"], **params) == body
        assert await client.customers.update(body["id"], **params) == body
        assert await client.customers.get(body["id"]) == body
    assert json.loads(create.calls.last.request.content) == {"name": body["name"], **params}
    assert json.loads(update.calls.last.request.content) == params


def local_tax_bodies(variant):
    decision, invoice = fixture("taxDecision"), fixture("invoice")
    if variant == "absent":
        return decision, invoice
    registration = dict(LOCAL_TAX_REGISTRATION)
    tax = dict(LOCAL_TAX)
    if variant == "future":
        registration.update(territory="future_territory", effectiveTo="2027-01-01")
        tax.update(code="future_local_tax", exemption="future_exemption")
    elif variant == "exempt":
        tax.update(rateCentipercent=0, amount=0, exemption="cgism_253")
    decision["sellerProfile"]["localTaxRegistrations"] = [registration]
    decision["lines"][0]["localTax"] = tax
    decision["totals"]["totalLocalTax"] = tax["amount"]
    invoice["items"][0]["localTax"] = tax
    invoice["totals"]["totalLocalTax"] = tax["amount"]
    return decision, invoice


def assert_local_tax_response(decision, invoice, variant):
    if variant == "absent":
        assert "localTaxRegistrations" not in decision["sellerProfile"]
        assert "localTax" not in decision["lines"][0]
        assert "totalLocalTax" not in decision["totals"]
        assert "localTax" not in invoice["items"][0]
        assert "totalLocalTax" not in invoice["totals"]
        return
    tax = decision["lines"][0]["localTax"]
    assert invoice["items"][0]["localTax"] == tax
    assert type(tax["amount"]) is int
    assert type(tax["rateCentipercent"]) is int
    for total in (decision["totals"]["totalLocalTax"], invoice["totals"]["totalLocalTax"]):
        assert type(total) is int
        assert total == tax["amount"]
    registration = decision["sellerProfile"]["localTaxRegistrations"][0]
    if variant == "future":
        assert tax["code"] == "future_local_tax"
        assert tax["exemption"] == "future_exemption"
        assert registration["territory"] == "future_territory"
        assert registration["effectiveTo"] == "2027-01-01"
    else:
        assert tax["exemption"] == ("cgism_253" if variant == "exempt" else None)
        assert registration["effectiveTo"] is None


@pytest.mark.parametrize("variant", ["absent", "charged", "exempt", "future"])
@respx.mock
def test_local_taxes_round_trip_in_decisions_and_invoices(variant):
    decision, invoice = local_tax_bodies(variant)
    respx.get(f"{DEFAULT_BASE_URL}/v1/tax-decisions/{decision['id']}").respond(json=decision)
    respx.get(f"{DEFAULT_BASE_URL}/v1/invoices/{invoice['id']}").respond(json=invoice)
    with facturino.Client("fac_test_corpus") as client:
        result = client.tax_decisions.get(decision["id"])
        document = client.invoices.get(invoice["id"])
    assert result == decision
    assert document == invoice
    assert_local_tax_response(result, document, variant)


@pytest.mark.parametrize("variant", ["absent", "charged", "exempt", "future"])
@respx.mock
async def test_async_local_taxes_round_trip_in_decisions_and_invoices(variant):
    decision, invoice = local_tax_bodies(variant)
    respx.get(f"{DEFAULT_BASE_URL}/v1/tax-decisions/{decision['id']}").respond(json=decision)
    respx.get(f"{DEFAULT_BASE_URL}/v1/invoices/{invoice['id']}").respond(json=invoice)
    async with facturino.AsyncClient("fac_test_corpus") as client:
        result = await client.tax_decisions.get(decision["id"])
        document = await client.invoices.get(invoice["id"])
    assert result == decision
    assert document == invoice
    assert_local_tax_response(result, document, variant)
