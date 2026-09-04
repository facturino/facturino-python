"""Tests for the Invoices resource."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import facturino
from facturino._client import DEFAULT_BASE_URL

API_KEY = "fac_test_abc123def456ghi789"
BASE = DEFAULT_BASE_URL


@pytest.fixture
def client():
    c = facturino.Client(API_KEY)
    yield c
    c.close()


class TestInvoiceCreate:
    @respx.mock
    def test_create_invoice(self, client):
        respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(201, json={
                "id": "inv_abc123",
                "object": "invoice",
                "status": "draft",
                "taxSource": "facturino",
                "customer": {"ref": "cus_xyz", "snapshot": {"name": "ACME"}},
                "totals": {"totalHT": "100.00", "totalTVA": "20.00", "totalTTC": "120.00"},
            })
        )

        invoice = client.invoices.create(
            customer="cus_xyz",
            taxDecisionId="taxdec_9c1f",
            decisionLines=[{"taxLineRef": "consulting", "unit": "hour"}],
        )

        assert invoice["id"] == "inv_abc123"
        assert invoice["status"] == "draft"

    @respx.mock
    def test_create_maps_customer_to_customer_id(self, client):
        route = respx.post(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(201, json={"id": "inv_new", "object": "invoice"})
        )

        client.invoices.create(
            customer="cus_123",
            tax_decision_id="taxdec_9c1f",
            decision_lines=[{"taxLineRef": "consulting", "unit": "hour"}],
        )

        request = route.calls[0].request
        body = request.read()
        import json
        parsed = json.loads(body)
        assert "customerId" in parsed
        assert parsed["customerId"] == "cus_123"
        assert "customer" not in parsed
        # The snake_case aliases reach the wire camelCase.
        assert parsed["taxDecisionId"] == "taxdec_9c1f"
        assert parsed["decisionLines"] == [{"taxLineRef": "consulting", "unit": "hour"}]
        assert "tax_decision_id" not in parsed
        assert "decision_lines" not in parsed

    def test_create_refuses_explicit_vat_lines(self, client):
        # No respx route: the refusal happens before any HTTP call.
        import pytest
        with pytest.raises(ValueError, match="'items' is not part"):
            client.invoices.create(
                customer="cus_123",
                taxDecisionId="taxdec_9c1f",
                decisionLines=[{"taxLineRef": "consulting", "unit": "hour"}],
                items=[{"description": "Test", "quantity": 1, "unit_price": 5000, "vat_rate": 2000}],
            )
        with pytest.raises(ValueError, match="'taxDecisionId' is required"):
            client.invoices.create(customer="cus_123", decisionLines=[{"taxLineRef": "x", "unit": "unit"}])


class TestInvoiceList:
    @respx.mock
    def test_list_returns_sync_page(self, client):
        respx.get(f"{BASE}/v1/invoices").mock(
            return_value=httpx.Response(200, json={
                "object": "list",
                "url": "/v1/invoices",
                "data": [
                    {"id": "inv_1", "object": "invoice", "status": "draft"},
                    {"id": "inv_2", "object": "invoice", "status": "finalized"},
                ],
                "has_more": False,
                "next_cursor": None,
            })
        )

        page = client.invoices.list(limit=10)
        assert len(page) == 2
        assert page.data[0]["id"] == "inv_1"
        assert not page.has_more

    @respx.mock
    def test_list_auto_pagination(self, client):
        # Page 1
        respx.get(f"{BASE}/v1/invoices").mock(
            side_effect=[
                httpx.Response(200, json={
                    "object": "list",
                    "url": "/v1/invoices",
                    "data": [{"id": "inv_1"}, {"id": "inv_2"}],
                    "has_more": True,
                    "next_cursor": "inv_2",
                }),
                httpx.Response(200, json={
                    "object": "list",
                    "url": "/v1/invoices",
                    "data": [{"id": "inv_3"}],
                    "has_more": False,
                    "next_cursor": None,
                }),
            ]
        )

        ids = [inv["id"] for inv in client.invoices.list(limit=2)]
        assert ids == ["inv_1", "inv_2", "inv_3"]


class TestInvoiceGet:
    @respx.mock
    def test_get_invoice(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_abc").mock(
            return_value=httpx.Response(200, json={
                "id": "inv_abc",
                "object": "invoice",
                "status": "finalized",
                "number": "FAC-2026-00001",
            })
        )

        invoice = client.invoices.get("inv_abc")
        assert invoice["id"] == "inv_abc"
        assert invoice["number"] == "FAC-2026-00001"

    @respx.mock
    def test_get_invoice_not_found(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_missing").mock(
            return_value=httpx.Response(404, json={
                "error": {
                    "type": "invalid_request_error",
                    "code": "resource_not_found",
                    "message": "No such invoice: inv_missing",
                }
            })
        )

        with pytest.raises(facturino.NotFoundError):
            client.invoices.get("inv_missing")


class TestBindTaxDecision:
    """Fiscalising a commercial draft that already exists — the quote cycle."""

    BOUND = {
        "id": "inv_converted",
        "object": "invoice",
        "status": "draft",
        "taxSource": "facturino",
        "taxDecisionId": "taxdec_1",
        "number": None,
    }

    @respx.mock
    def test_binds_the_decision_to_the_existing_draft(self, client):
        route = respx.post(f"{BASE}/v1/invoices/inv_converted/bind-tax-decision").mock(
            return_value=httpx.Response(200, json=self.BOUND)
        )

        result = client.invoices.bind_tax_decision(
            "inv_converted",
            tax_decision_id="taxdec_1",
            decision_lines=[{"taxLineRef": "l1", "unit": "unit"}],
        )

        assert result["taxDecisionId"] == "taxdec_1"
        assert result["taxSource"] == "facturino"
        # Binding freezes the VAT; finalize() issues the invoice.
        assert result["status"] == "draft"
        assert json.loads(route.calls[0].request.content) == {
            "taxDecisionId": "taxdec_1",
            "decisionLines": [{"taxLineRef": "l1", "unit": "unit"}],
        }

    @respx.mock
    def test_accepts_the_camel_case_aliases_too(self, client):
        route = respx.post(f"{BASE}/v1/invoices/inv_converted/bind-tax-decision").mock(
            return_value=httpx.Response(200, json=self.BOUND)
        )

        client.invoices.bind_tax_decision(
            "inv_converted",
            taxDecisionId="taxdec_1",
            decisionLines=[{"taxLineRef": "l1", "unit": "unit"}],
        )

        assert json.loads(route.calls[0].request.content)["taxDecisionId"] == "taxdec_1"

    @respx.mock
    def test_closes_the_quote_cycle_on_one_invoice(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_converted/bind-tax-decision").mock(
            return_value=httpx.Response(200, json=self.BOUND)
        )
        respx.post(f"{BASE}/v1/invoices/inv_converted/finalize").mock(
            return_value=httpx.Response(200, json={**self.BOUND, "status": "finalized", "number": "FAC-00001"})
        )

        bound = client.invoices.bind_tax_decision(
            "inv_converted",
            tax_decision_id="taxdec_1",
            decision_lines=[{"taxLineRef": "l1", "unit": "unit"}],
        )
        finalized = client.invoices.finalize(bound["id"])

        # One document throughout: no second invoice was ever created.
        assert finalized["id"] == "inv_converted"
        assert finalized["number"] == "FAC-00001"

    @respx.mock
    def test_finalize_sends_no_body_without_a_collection(self, client):
        route = respx.post(f"{BASE}/v1/invoices/inv_1/finalize").mock(
            return_value=httpx.Response(200, json={"id": "inv_1", "status": "finalized"})
        )

        client.invoices.finalize("inv_1")

        assert route.calls[0].request.content in (b"", b"null")

    @respx.mock
    def test_finalize_issues_an_already_collected_invoice_as_settled(self, client):
        route = respx.post(f"{BASE}/v1/invoices/inv_1/finalize").mock(
            return_value=httpx.Response(
                200,
                json={"id": "inv_1", "status": "paid", "number": "FAC-00001"},
            )
        )

        result = client.invoices.finalize(
            "inv_1",
            payment={
                "amount": 120000,
                "method": "card",
                "reference": "ch_3Kj9aLZ",
                # snake_case alias, exactly as payments.create accepts it
                "paid_at": "2026-05-10T12:00:00.000Z",
            },
        )

        assert result["status"] == "paid"
        assert json.loads(route.calls[0].request.content) == {
            "payment": {
                "amount": 120000,
                "method": "card",
                "reference": "ch_3Kj9aLZ",
                "paidAt": "2026-05-10T12:00:00.000Z",
            }
        }

    def test_refuses_locally_without_a_decision(self, client):
        with pytest.raises(ValueError, match="taxDecisionId"):
            client.invoices.bind_tax_decision(
                "inv_converted", decision_lines=[{"taxLineRef": "l1", "unit": "unit"}]
            )

    def test_refuses_locally_an_empty_presentation(self, client):
        with pytest.raises(ValueError, match="decisionLines"):
            client.invoices.bind_tax_decision(
                "inv_converted", tax_decision_id="taxdec_1", decision_lines=[]
            )


class TestInvoiceActions:
    @respx.mock
    def test_finalize(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/finalize").mock(
            return_value=httpx.Response(200, json={
                "id": "inv_1",
                "object": "invoice",
                "status": "finalized",
                "number": "FAC-2026-00001",
            })
        )

        result = client.invoices.finalize("inv_1")
        assert result["status"] == "finalized"
        assert result["number"] is not None

    @respx.mock
    def test_send(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/send").mock(
            return_value=httpx.Response(202, json={
                "id": "inv_1",
                "object": "invoice",
                "status": "sending",
            })
        )

        result = client.invoices.send("inv_1")
        assert result["status"] == "sending"

    @respx.mock
    def test_clone(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/clone").mock(
            return_value=httpx.Response(201, json={
                "id": "inv_clone_1",
                "object": "invoice",
                "status": "draft",
            })
        )

        result = client.invoices.clone("inv_1")
        assert result["id"] == "inv_clone_1"
        assert result["status"] == "draft"

    @respx.mock
    def test_remind(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/remind").mock(
            return_value=httpx.Response(202, json={
                "id": "inv_1",
                "object": "invoice",
                "reminder_sent": True,
            })
        )

        result = client.invoices.remind("inv_1")
        assert result["reminder_sent"] is True

    @respx.mock
    def test_delete(self, client):
        respx.delete(f"{BASE}/v1/invoices/inv_1").mock(
            return_value=httpx.Response(204)
        )

        # Should not raise
        client.invoices.delete("inv_1")

    @respx.mock
    def test_update(self, client):
        respx.patch(f"{BASE}/v1/invoices/inv_1").mock(
            return_value=httpx.Response(200, json={
                "id": "inv_1",
                "object": "invoice",
                "status": "draft",
                "notes": "Updated notes",
            })
        )

        result = client.invoices.update("inv_1", notes="Updated notes")
        assert result["notes"] == "Updated notes"


class TestInvoiceDocuments:
    @respx.mock
    def test_get_pdf_cached(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/pdf").mock(
            return_value=httpx.Response(200, json={
                "url": "https://storage.example.com/invoice.pdf",
                "expires_in": 900,
            })
        )

        result = client.invoices.get_pdf("inv_1")
        assert "url" in result
        assert result["expires_in"] == 900

    @respx.mock
    def test_get_pdf_async_job(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/pdf").mock(
            return_value=httpx.Response(202, json={
                "id": "job_abc",
                "object": "job",
                "type": "pdf",
                "status": "pending",
            })
        )

        result = client.invoices.get_pdf("inv_1")
        assert result["object"] == "job"
        assert result["status"] == "pending"

    @respx.mock
    def test_get_xml(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/xml").mock(
            return_value=httpx.Response(200, text="<Invoice>...</Invoice>", headers={"content-type": "application/xml"})
        )

        xml = client.invoices.get_xml("inv_1")
        assert "<Invoice>" in xml

    @respx.mock
    def test_get_status(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/status").mock(
            return_value=httpx.Response(200, json={
                "status": "deposited",
                "einvoicing": {"paStatus": "deposited", "paId": "pa_123"},
            })
        )

        result = client.invoices.get_status("inv_1")
        assert result["status"] == "deposited"

    @respx.mock
    def test_verify(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/verify").mock(
            return_value=httpx.Response(200, json={
                "id": "inv_1",
                "verified": True,
                "chain_length": 5,
            })
        )

        result = client.invoices.verify("inv_1")
        assert result["verified"] is True

    @respx.mock
    def test_list_events(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/events").mock(
            return_value=httpx.Response(200, json={
                "object": "list",
                "data": [{"status": "draft", "timestamp": "2026-01-01T00:00:00Z"}],
            })
        )

        result = client.invoices.list_events("inv_1")
        assert len(result["data"]) == 1

    @respx.mock
    def test_get_audit_trail(self, client):
        respx.get(f"{BASE}/v1/invoices/inv_1/audit-trail").mock(
            return_value=httpx.Response(200, json={
                "object": "list",
                "data": [{"action": "create"}],
                "has_more": False,
            })
        )

        result = client.invoices.get_audit_trail("inv_1")
        assert result["data"][0]["action"] == "create"

    @respx.mock
    def test_generate_audit_trail_pdf(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/audit-trail/pdf").mock(
            return_value=httpx.Response(202, json={
                "id": "job_xyz",
                "object": "job",
                "type": "audit_trail_pdf",
                "status": "pending",
            })
        )

        result = client.invoices.generate_audit_trail_pdf("inv_1")
        assert result["type"] == "audit_trail_pdf"

    @respx.mock
    def test_create_payment_link(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/payment-link").mock(
            return_value=httpx.Response(200, json={
                "object": "payment_link",
                "url": "https://checkout.stripe.com/pay/xxx",
                "session_id": "cs_test_xxx",
            })
        )

        result = client.invoices.create_payment_link("inv_1", success_url="https://example.com/ok")
        assert "url" in result

    @respx.mock
    def test_create_payment_token(self, client):
        respx.post(f"{BASE}/v1/invoices/inv_1/payment-token").mock(
            return_value=httpx.Response(200, json={
                "object": "payment_token",
                "token": "abc123",
                "pay_url": "/pay/abc123",
                "expires_at": "2026-01-02T00:00:00Z",
            })
        )

        result = client.invoices.create_payment_token("inv_1")
        assert result["token"] == "abc123"

    @respx.mock
    def test_record_payment_paypal(self, client):
        import json as _json
        route = respx.post(f"{BASE}/v1/invoices/inv_1/payments").mock(
            return_value=httpx.Response(201, json={
                "id": "pay_pp", "object": "payment", "amount": 10000, "method": "paypal",
            })
        )
        result = client.payments.create("inv_1", amount=10000, method="paypal", paid_at="2026-03-15")
        assert result["method"] == "paypal"
        sent = _json.loads(route.calls.last.request.content)
        assert sent["method"] == "paypal"
