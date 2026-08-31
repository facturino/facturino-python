"""Tests for the resources added in the 100% API coverage pass:
``billing``, ``reference``, ``usage`` and ``validate``.

Tests exercise the request path, query / body shape and the snake_case
to camelCase mapping the SDK does on behalf of the caller.
"""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino

BASE = "https://facturino.com/api"


# ─── billing ──────────────────────────────────────────────────────────


@respx.mock
def test_billing_retrieve_subscription() -> None:
    payload = {
        "object": "subscription",
        "plan": "pro",
        "cycle": "monthly",
        "status": "active",
    }
    route = respx.get(f"{BASE}/v1/billing/subscription").mock(
        return_value=httpx.Response(200, json=payload)
    )

    client = facturino.Client("fac_test_abc")
    assert client.billing.retrieve_subscription() == payload
    assert route.called


@respx.mock
def test_billing_invoices_list_and_pdf() -> None:
    respx.get(f"{BASE}/v1/billing/invoices").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    respx.get(f"{BASE}/v1/billing/invoices/in_123/pdf").mock(
        return_value=httpx.Response(200, json={"url": "https://signed.example/pdf"})
    )

    client = facturino.Client("fac_test_abc")
    listed = client.billing.list_invoices(limit=5)
    pdf = client.billing.get_invoice_pdf("in_123")

    assert listed["has_more"] is False
    assert pdf["url"].startswith("https://")


# ─── usage ────────────────────────────────────────────────────────────


@respx.mock
def test_usage_retrieve() -> None:
    respx.get(f"{BASE}/v1/usage").mock(
        return_value=httpx.Response(
            200,
            json={
                "plan": "pro",
                "period": {"start": "2026-05-01", "end": "2026-05-31"},
                "invoicesIssued": {"used": 12, "limit": 1000},
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    snap = client.usage.retrieve()
    assert snap["plan"] == "pro"
    assert snap["invoicesIssued"]["used"] == 12


# ─── health ───────────────────────────────────────────────────────────


@respx.mock
def test_health_check() -> None:
    route = respx.get(f"{BASE}/v1/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "apiVersion": "2026-09-01"})
    )

    client = facturino.Client("fac_test_abc")
    result = client.health.check()

    assert result["status"] == "ok"
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_async_health_check() -> None:
    respx.get(f"{BASE}/v1/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.health.check()
    assert result["status"] == "ok"


# ─── validate ─────────────────────────────────────────────────────────


@respx.mock
def test_validate_siret() -> None:
    route = respx.post(f"{BASE}/v1/validate").mock(
        return_value=httpx.Response(200, json={"valid": True, "kind": "siret"})
    )

    client = facturino.Client("fac_test_abc")
    result = client.validate.run(kind="siret", value="44306184100047")

    assert result["valid"] is True
    body = route.calls.last.request.read().decode()
    assert "siret" in body and "44306184100047" in body


# ─── reference ────────────────────────────────────────────────────────


@respx.mock
def test_reference_legal_forms_and_naf() -> None:
    respx.get(f"{BASE}/v1/reference/legal-forms").mock(
        return_value=httpx.Response(200, json={"data": [{"code": "5710", "label": "SAS"}], "has_more": False})
    )
    respx.get(f"{BASE}/v1/reference/naf-codes").mock(
        return_value=httpx.Response(200, json={"data": [{"code": "62.01Z"}], "has_more": False})
    )

    client = facturino.Client("fac_test_abc")
    forms = client.reference.list_legal_forms(search="SAS")
    naf = client.reference.list_naf_codes(search="conseil")

    assert forms.data[0]["code"] == "5710"
    assert naf.data[0]["code"] == "62.01Z"


# ─── async parity ─────────────────────────────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_async_billing_subscription() -> None:
    respx.get(f"{BASE}/v1/billing/subscription").mock(
        return_value=httpx.Response(200, json={"plan": "pro"})
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        sub = await client.billing.retrieve_subscription()
    assert sub["plan"] == "pro"


@respx.mock
@pytest.mark.asyncio
async def test_async_validate_run() -> None:
    respx.post(f"{BASE}/v1/validate").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.validate.run(kind="iban", value="FR7630006000011234567890189")
    assert result["valid"] is True


@respx.mock
@pytest.mark.asyncio
async def test_async_reference_lists() -> None:
    respx.get(f"{BASE}/v1/reference/legal-forms").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        page = await client.reference.list_legal_forms(limit=5)
    assert page.data == []
