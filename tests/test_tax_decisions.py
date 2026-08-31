"""Contract tests for the tax-decisions resource and decision-backed documents.

They assert the exact path, headers and JSON body the SDK produces. Nothing
leaves the machine: respx intercepts the transport.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import facturino
from facturino import ConflictError
from facturino._client import DEFAULT_BASE_URL

API_KEY = "fac_test_abc123def456ghi789"
BASE = DEFAULT_BASE_URL

FINAL_DECISION = {
    "id": "taxdec_9c1f",
    "object": "tax_decision",
    "status": "final",
    "taxSource": "facturino",
    "customerId": "cus_8f2k4m9n",
    "currency": "eur",
    "priceMode": "tax_exclusive",
    "effectiveAt": "2026-09-15",
    "expired": False,
    "rulesVersion": "fr-vat-2021-07-01",
    "operationFingerprint": "sha256:op",
    "totals": {"totalHT": 2900, "totalVAT": 580, "totalTTC": 3480},
    "amountToCharge": 3480,
    "invoiceChannel": "einvoicing",
    "transactionReporting": "none",
    "paymentReporting": "fr212",
    "foreignTaxReviewRequired": False,
    "vies": None,
    "issues": [],
    "obligationReasons": [{"axis": "paymentReporting", "code": "fr212_b2b"}],
    "retryOfTaxDecisionId": None,
}

DECISION_PARAMS = {
    "tax_source": "facturino",
    "customer_id": "cus_8f2k4m9n",
    "effective_at": "2026-09-15",
    "currency": "eur",
    "price_mode": "tax_exclusive",
    "lines": [{
        "reference": "abo-pro",
        "description": "Abonnement Pro",
        "category": "electronically_supplied_services",
        "rate_category": "standard",
        "unit_amount": 2900,
        "quantity": "1",
    }],
}

EXPECTED_BODY = {
    "taxSource": "facturino",
    "customerId": "cus_8f2k4m9n",
    "effectiveAt": "2026-09-15",
    "currency": "eur",
    "priceMode": "tax_exclusive",
    "lines": [{
        "reference": "abo-pro",
        "description": "Abonnement Pro",
        "category": "electronically_supplied_services",
        "rateCategory": "standard",
        "unitAmount": 2900,
        "quantity": "1",
    }],
}


@pytest.fixture
def client():
    c = facturino.Client(API_KEY)
    yield c
    c.close()


class TestResourceSurface:
    def test_exposed_on_both_clients(self, client):
        assert client.tax_decisions is not None
        async_client = facturino.AsyncClient(API_KEY)
        assert async_client.tax_decisions is not None

    def test_no_mutation_method(self, client):
        # A decision is immutable: there is nothing to update or delete.
        for forbidden in ("update", "patch", "delete", "cancel"):
            assert not hasattr(client.tax_decisions, forbidden)


class TestCreate:
    def test_refuses_an_empty_idempotency_key(self, client):
        with pytest.raises(ValueError, match="Idempotency-Key is required"):
            client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="   ")

    def test_refuses_a_key_longer_than_the_api_accepts(self, client):
        # Checked locally: an over-long key fails without a round trip.
        with pytest.raises(ValueError, match="at most 255 characters"):
            client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="k" * 256)

    @respx.mock
    def test_accepts_a_key_of_exactly_the_maximum_length(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )
        client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="k" * 255)
        assert route.call_count == 1

    @respx.mock
    def test_sends_the_current_dated_contract_version(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )
        client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="order-version")
        assert route.calls.last.request.headers["Facturino-Version"] == "2026-09-01"

    @respx.mock
    def test_returns_the_decision_on_a_200_replay_exactly_as_on_a_201(self, client):
        respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )
        created = client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="order-replay")

        respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(200, json=FINAL_DECISION)
        )
        replayed = client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="order-replay")

        assert replayed == created

    @respx.mock
    def test_surfaces_a_409_as_a_conflict_error(self, client):
        respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(409, json={"error": {
                "type": "invalid_request_error",
                "code": "conflict",
                "message": "This Idempotency-Key was already used with a different request body.",
            }})
        )
        with pytest.raises(ConflictError) as excinfo:
            client.tax_decisions.create(**DECISION_PARAMS, idempotency_key="order-replay")
        assert excinfo.value.status_code == 409

    @respx.mock
    def test_posts_to_the_exact_path_with_the_exact_body(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )

        decision = client.tax_decisions.create(
            **DECISION_PARAMS, idempotency_key="order-4711"
        )

        request = route.calls.last.request
        assert request.url.path == "/api/v1/tax-decisions"
        assert json.loads(request.content) == EXPECTED_BODY
        assert request.headers["Idempotency-Key"] == "order-4711"
        assert decision["amountToCharge"] == 3480

    @respx.mock
    def test_accepts_camel_case_as_well(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )

        client.tax_decisions.create(
            taxSource="facturino",
            customerId="cus_8f2k4m9n",
            effectiveAt="2026-09-15",
            currency="eur",
            priceMode="tax_exclusive",
            lines=EXPECTED_BODY["lines"],
            idempotency_key="order-camel",
        )

        assert json.loads(route.calls.last.request.content) == EXPECTED_BODY

    @respx.mock
    def test_keeps_quantities_as_strings_and_amounts_as_integers(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )

        params = dict(DECISION_PARAMS)
        params["lines"] = [{
            **DECISION_PARAMS["lines"][0],
            "quantity": "2.500000",
            "discount": {"type": "percent", "value": 2500},
        }]
        client.tax_decisions.create(**params, idempotency_key="order-quantity")

        line = json.loads(route.calls.last.request.content)["lines"][0]
        # A float quantity would not survive: 0.1 + 0.2 is not 0.3.
        assert isinstance(line["quantity"], str)
        assert line["quantity"] == "2.500000"
        assert isinstance(line["unitAmount"], int)
        # Centi-percent: 2500 is 25.00 %.
        assert line["discount"] == {"type": "percent", "value": 2500}

    @respx.mock
    def test_integration_source_lines_carry_their_supplied_vat(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json={
                **FINAL_DECISION, "taxSource": "integration",
            })
        )

        decision = client.tax_decisions.create(
            tax_source="integration",
            customer_id="cus_8f2k4m9n",
            effective_at="2026-09-15",
            currency="eur",
            price_mode="tax_exclusive",
            lines=[
                {
                    "reference": "conseil",
                    "description": "Conseil",
                    "category": "services",
                    "unit_amount": 2900,
                    "quantity": "1",
                    "vat_rate": 2000,
                    "vat_code": "S",
                },
                {
                    "reference": "formation",
                    "description": "Formation exportée",
                    "category": "services",
                    "unit_amount": 5000,
                    "quantity": "1",
                    "vat_rate": 0,
                    "vat_code": "G",
                    "vatex_code": "VATEX-EU-G",
                    "place_of_supply": "GB",
                },
            ],
            idempotency_key="order-integration-1",
        )

        body = json.loads(route.calls.last.request.content)
        assert body["taxSource"] == "integration"
        assert body["lines"][0] == {
            "reference": "conseil", "description": "Conseil", "category": "services",
            "unitAmount": 2900, "quantity": "1", "vatRate": 2000, "vatCode": "S",
        }
        assert body["lines"][1]["vatRate"] == 0
        assert body["lines"][1]["vatexCode"] == "VATEX-EU-G"
        assert body["lines"][1]["placeOfSupply"] == "GB"
        assert decision["taxSource"] == "integration"

    @respx.mock
    def test_evidence_travels_without_raw_signal(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )

        client.tax_decisions.create(
            **DECISION_PARAMS,
            location_evidence=[{
                "kind": "ip_geolocation",
                "country": "FR",
                "postal_code": "75002",
                "third_party": True,
                "source": "psp",
                "collected_at": "2026-09-15",
                "reference": "ch_3Kj9aLZ",
            }],
            non_eu_business_evidence={
                "kind": "vat_or_similar_number",
                "reference": "CH-123456",
                "issued_by_country": "CH",
                "reasonable_verification_performed": True,
                "collected_at": "2026-09-15",
            },
            idempotency_key="order-evidence",
        )

        raw = route.calls.last.request.content.decode()
        body = json.loads(raw)
        assert body["locationEvidence"][0] == {
            "kind": "ip_geolocation", "country": "FR", "postalCode": "75002",
            "thirdParty": True, "source": "psp", "collectedAt": "2026-09-15",
            "reference": "ch_3Kj9aLZ",
        }
        assert body["nonEuBusinessEvidence"]["reasonableVerificationPerformed"] is True
        # The territorial signal travels, never the raw one.
        for forbidden in ('"ip"', '"payload"', '"iban"'):
            assert forbidden not in raw

    @respx.mock
    def test_non_final_decision_has_null_amounts(self, client):
        respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json={
                "id": "taxdec_pending",
                "object": "tax_decision",
                "status": "pending_verification",
                "totals": None,
                "amountToCharge": None,
                "invoiceChannel": None,
                "transactionReporting": None,
                "paymentReporting": None,
                "issues": [{"code": "vies_unavailable", "message": "VIES is unreachable."}],
            })
        )

        decision = client.tax_decisions.create(
            **DECISION_PARAMS, idempotency_key="order-pending"
        )

        assert decision["status"] == "pending_verification"
        # None, never 0: absent is not "nothing to charge".
        assert decision["amountToCharge"] is None
        assert decision["totals"] is None
        assert decision["issues"][0]["code"] == "vies_unavailable"

    @respx.mock
    def test_retry_carries_lineage_and_keeps_the_operation(self, client):
        route = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json={
                **FINAL_DECISION, "retryOfTaxDecisionId": "taxdec_previous"
            })
        )

        decision = client.tax_decisions.create(
            **DECISION_PARAMS,
            retry_of_tax_decision_id="taxdec_previous",
            location_evidence=[{
                "kind": "billing_address", "country": "FR", "third_party": False,
                "source": "declared", "collected_at": "2026-09-15",
            }],
            idempotency_key="order-retry",
        )

        body = json.loads(route.calls.last.request.content)
        assert body["retryOfTaxDecisionId"] == "taxdec_previous"
        # Only the evidence is added; the commercial operation is identical.
        assert body["lines"] == EXPECTED_BODY["lines"]
        assert decision["retryOfTaxDecisionId"] == "taxdec_previous"


class TestRetrieve:
    @respx.mock
    def test_gets_by_id(self, client):
        route = respx.get(f"{BASE}/v1/tax-decisions/taxdec_9c1f").mock(
            return_value=httpx.Response(200, json=FINAL_DECISION)
        )

        decision = client.tax_decisions.retrieve("taxdec_9c1f")

        assert route.calls.last.request.url.path == "/api/v1/tax-decisions/taxdec_9c1f"
        assert decision["id"] == "taxdec_9c1f"
        assert decision["obligationReasons"][0]["axis"] == "paymentReporting"

    @respx.mock
    def test_get_is_an_alias(self, client):
        route = respx.get(f"{BASE}/v1/tax-decisions/taxdec_9c1f").mock(
            return_value=httpx.Response(200, json=FINAL_DECISION)
        )
        client.tax_decisions.get("taxdec_9c1f")
        assert route.called


class TestAsyncSurface:
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_create_and_retrieve(self):
        create = respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )
        read = respx.get(f"{BASE}/v1/tax-decisions/taxdec_9c1f").mock(
            return_value=httpx.Response(200, json=FINAL_DECISION)
        )

        client = facturino.AsyncClient(API_KEY)
        try:
            decision = await client.tax_decisions.create(
                **DECISION_PARAMS, idempotency_key="order-4711"
            )
            assert decision["amountToCharge"] == 3480
            assert json.loads(create.calls.last.request.content) == EXPECTED_BODY
            assert create.calls.last.request.headers["Idempotency-Key"] == "order-4711"

            again = await client.tax_decisions.retrieve("taxdec_9c1f")
            assert again["id"] == "taxdec_9c1f"
            assert read.called
        finally:
            await client.close()


class TestDecisionBackedDocuments:
    @respx.mock
    def test_invoice_backed_by_a_decision(self, client):
        route = respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(201, json={
                "id": "inv_1", "object": "invoice", "status": "draft",
                "documentStatus": "draft", "transmissionStatus": "not_applicable",
                "paymentStatus": "unpaid", "taxSource": "facturino",
                "taxDecisionId": "taxdec_9c1f",
            })
        )

        invoice = client.invoices.create(
            idempotency_key="decided-invoice-1",
            customerId="cus_8f2k4m9n",
            taxDecisionId="taxdec_9c1f",
            decisionLines=[{"taxLineRef": "abo-pro", "unit": "month"}],
            buyer={"companyName": "ACME SAS"},
            dates={"issued": "2026-09-15", "due": "2026-10-15"},
            payment={"terms": "30 jours", "termsDays": 30, "method": "transfer"},
        )

        raw = route.calls.last.request.content.decode()
        body = json.loads(raw)
        assert body["taxDecisionId"] == "taxdec_9c1f"
        assert body["decisionLines"] == [{"taxLineRef": "abo-pro", "unit": "month"}]
        # The historical `lines` field never travels alongside a decision.
        assert "lines" not in body
        assert '"vatRate"' not in raw
        assert route.calls.last.request.headers["Idempotency-Key"] == "decided-invoice-1"

        assert invoice["taxSource"] == "facturino"
        assert invoice["documentStatus"] == "draft"
        assert invoice["paymentStatus"] == "unpaid"

    def test_refuses_explicit_vat_lines_locally(self, client):
        # No respx route on purpose: the refusal must happen before any HTTP call.
        # Hostile: the EMPTY list is refused too — presence of the key, not its
        # content, is the rule.
        for field in ("lines", "items"):
            for value in ([{}], []):
                with pytest.raises(ValueError, match=f"'{field}' is not part"):
                    client.invoices.create(
                        customerId="cus_8f2k4m9n",
                        taxDecisionId="taxdec_9c1f",
                        decisionLines=[{"taxLineRef": "abo-pro", "unit": "month"}],
                        buyer={"companyName": "ACME SAS"},
                        dates={"issued": "2026-09-15", "due": "2026-10-15"},
                        payment={"terms": "30 jours", "termsDays": 30, "method": "transfer"},
                        **{field: value},
                    )

    def test_refuses_an_invoice_without_a_decision(self, client):
        # No route either: nothing must leave the machine.
        with pytest.raises(ValueError, match="'taxDecisionId' is required"):
            client.invoices.create(
                customerId="cus_8f2k4m9n",
                decisionLines=[{"taxLineRef": "abo-pro", "unit": "month"}],
                buyer={"companyName": "ACME SAS"},
                dates={"issued": "2026-09-15", "due": "2026-10-15"},
                payment={"terms": "30 jours", "termsDays": 30, "method": "transfer"},
            )
        with pytest.raises(ValueError, match="'decisionLines' is required"):
            client.invoices.create(
                customerId="cus_8f2k4m9n",
                taxDecisionId="taxdec_9c1f",
                buyer={"companyName": "ACME SAS"},
                dates={"issued": "2026-09-15", "due": "2026-10-15"},
                payment={"terms": "30 jours", "termsDays": 30, "method": "transfer"},
            )

    @respx.mock
    def test_deposits_and_schedule_travel_with_the_decision(self, client):
        route = respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(201, json={"id": "inv_2", "object": "invoice"})
        )

        client.invoices.create(
            idempotency_key="decided-invoice-2",
            customerId="cus_8f2k4m9n",
            taxDecisionId="taxdec_9c1f",
            decisionLines=[{"taxLineRef": "abo-pro", "unit": "month"}],
            buyer={"companyName": "ACME SAS"},
            dates={"issued": "2026-09-15", "due": "2026-10-15"},
            payment={"terms": "30 jours", "termsDays": 30, "method": "transfer"},
            deposits=[{"invoiceId": "inv_dep"}],
            schedule=[
                {"amount": 1740, "dueDate": "2026-10-15"},
                {"amount": 1740, "dueDate": "2026-11-15"},
            ],
        )

        # Both settle SERVER-SIDE against the decided amount; the SDK only
        # forwards them.
        body = json.loads(route.calls.last.request.content)
        assert body["deposits"] == [{"invoiceId": "inv_dep"}]
        assert [i["amount"] for i in body["schedule"]] == [1740, 1740]

    @respx.mock
    def test_invoice_exposes_the_three_axes(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1").mock(
            return_value=httpx.Response(200, json={
                "id": "inv_1", "object": "invoice", "status": "deposited",
                "documentStatus": "finalized", "transmissionStatus": "deposited",
                "transmissionDetail": None, "paymentStatus": "partially_paid",
            })
        )

        invoice = client.invoices.get("inv_1")

        # A collection never moves the transmission axis; `status` stays
        # populated as their projection.
        assert invoice["status"] == "deposited"
        assert invoice["documentStatus"] == "finalized"
        assert invoice["transmissionStatus"] == "deposited"
        assert invoice["paymentStatus"] == "partially_paid"

    @respx.mock
    def test_credit_note_uses_credited_lines(self, client):
        route = respx.post(f"{BASE}/v1/credit-notes").mock(
            return_value=httpx.Response(201, json={
                "id": "crn_1", "object": "credit_note", "status": "draft",
                "taxSource": "facturino", "originalInvoiceId": "inv_1",
                "originalTaxDecisionId": "taxdec_9c1f",
            })
        )

        credit_note = client.credit_notes.create(
            idempotency_key="decided-credit-note-1",
            relatedInvoiceId="inv_1",
            creditNoteType="partial",
            reasonCode="quality",
            creditedLines=[{"taxLineRef": "abo-pro", "amountTTC": 1200}],
        )

        body = json.loads(route.calls.last.request.content)
        assert body["creditedLines"] == [{"taxLineRef": "abo-pro", "amountTTC": 1200}]
        # The VAT is inherited from the invoice snapshot, never restated.
        assert "items" not in body
        assert route.calls.last.request.headers["Idempotency-Key"] == "decided-credit-note-1"
        assert credit_note["originalTaxDecisionId"] == "taxdec_9c1f"

    @respx.mock
    def test_recurring_schedule_sends_tax_inputs(self, client):
        route = respx.post(f"{BASE}/v1/recurring-invoices").mock(
            return_value=httpx.Response(201, json={"id": "rin_1", "object": "recurring_invoice"})
        )

        client.recurring_invoices.create(
            idempotency_key="decided-recurring-1",
            customerId="cus_1",
            frequency="monthly",
            startDate="2026-09-01",
            nextGenerationDate="2026-09-01",
            taxInputs={
                "priceMode": "tax_exclusive",
                "lines": [{
                    "reference": "abo-pro", "description": "Abonnement Pro",
                    "category": "electronically_supplied_services",
                    "rateCategory": "standard", "unitAmount": 2900,
                    "quantity": "1", "unit": "month",
                }],
            },
            templateInvoice={"paymentTermsDays": 30},
        )

        raw = route.calls.last.request.content.decode()
        body = json.loads(raw)
        assert body["taxInputs"]["priceMode"] == "tax_exclusive"
        assert body["taxInputs"]["lines"][0]["quantity"] == "1"
        # No decision id travels: each occurrence is decided on its own date.
        assert "taxDecisionId" not in raw
        assert "items" not in body["templateInvoice"]
        assert route.calls.last.request.headers["Idempotency-Key"] == "decided-recurring-1"


class TestParityGuard:
    def test_the_fiscal_surface_stays_exposed(self, client):
        # If this fails, the resource or one of its methods was dropped, which
        # would silently remove the fiscal contract from the SDK.
        for method in ("create", "retrieve", "get"):
            assert callable(getattr(client.tax_decisions, method))

        async_client = facturino.AsyncClient(API_KEY)
        for method in ("create", "retrieve", "get"):
            assert callable(getattr(async_client.tax_decisions, method))

    @respx.mock
    def test_the_critical_decision_fields_stay_readable(self, client):
        respx.post(f"{BASE}/v1/tax-decisions").mock(
            return_value=httpx.Response(201, json=FINAL_DECISION)
        )
        decision = client.tax_decisions.create(
            **DECISION_PARAMS, idempotency_key="order-parity"
        )

        for field in (
            "status", "amountToCharge", "totals", "invoiceChannel",
            "transactionReporting", "paymentReporting", "foreignTaxReviewRequired",
            "retryOfTaxDecisionId", "expired", "rulesVersion",
            "operationFingerprint", "obligationReasons", "vies", "issues",
        ):
            assert field in decision, f"{field} disappeared from the decision"
