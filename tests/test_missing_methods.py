"""Tests for the methods backfilled to reach actual 100% API coverage:

- Account: schedule_deletion, cancel_deletion, request_export,
  download_export, update_notifications
- Companies: create, update_invoicing_settings, add_milestone
- Invoices: create_portal_link
"""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino


BASE = "https://facturino.com/api"


# ─── account — RGPD lifecycle ─────────────────────────────────────────


@respx.mock
def test_account_schedule_deletion() -> None:
    respx.post(f"{BASE}/v1/account/schedule-deletion").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "account_deletion",
                "deletionScheduledAt": "2026-06-19T00:00:00.000Z",
                "message": "Account scheduled for deletion in 30 days.",
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.account.schedule_deletion()
    assert result["deletionScheduledAt"].startswith("2026-")


@respx.mock
def test_account_cancel_deletion() -> None:
    respx.post(f"{BASE}/v1/account/cancel-deletion").mock(
        return_value=httpx.Response(
            200, json={"object": "account_deletion", "deletionScheduledAt": None}
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.account.cancel_deletion()
    assert result["deletionScheduledAt"] is None


@respx.mock
def test_account_request_and_download_export() -> None:
    respx.post(f"{BASE}/v1/account/export").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "account_export",
                "exportId": "rgpdexp_abc",
                "status": "pending",
                "message": "Export is being prepared.",
            },
        )
    )
    respx.get(f"{BASE}/v1/account/exports/rgpdexp_abc/download").mock(
        return_value=httpx.Response(
            200, json={"url": "https://signed.example/export.zip", "expiresAt": "2026-05-20T12:05Z"}
        )
    )

    client = facturino.Client("fac_test_abc")
    started = client.account.request_export()
    assert started["exportId"] == "rgpdexp_abc"

    download = client.account.download_export("rgpdexp_abc")
    assert download["url"].startswith("https://")


@respx.mock
def test_account_update_notifications() -> None:
    route = respx.patch(f"{BASE}/v1/account/notifications").mock(
        return_value=httpx.Response(200, json={"invoicePaid": False, "productNews": True})
    )

    client = facturino.Client("fac_test_abc")
    result = client.account.update_notifications(invoicePaid=False, productNews=True)

    assert result["invoicePaid"] is False
    body = route.calls.last.request.read().decode()
    assert "invoicePaid" in body and "false" in body.lower()


# ─── companies — backfilled methods ───────────────────────────────────


@respx.mock
def test_companies_create_under_plan_quota() -> None:
    route = respx.post(f"{BASE}/v1/companies").mock(
        return_value=httpx.Response(200, json={"id": "comp_new", "name": "ACME SAS"})
    )

    client = facturino.Client("fac_test_abc")
    result = client.companies.create(
        name="ACME SAS",
        siret="44306184100047",
        address={
            "line1": "12 rue de Rivoli",
            "postalCode": "75001",
            "city": "Paris",
            "countryCode": "FR",
        },
        vatRegime="normal",
    )

    assert result["id"] == "comp_new"
    body = route.calls.last.request.read().decode()
    assert "44306184100047" in body


@respx.mock
def test_companies_update_invoicing_settings() -> None:
    route = respx.patch(f"{BASE}/v1/companies/comp_x/invoicing-settings").mock(
        return_value=httpx.Response(200, json={"id": "comp_x", "vatRegime": "franchise"})
    )

    client = facturino.Client("fac_test_abc")
    result = client.companies.update_invoicing_settings("comp_x", vatRegime="franchise")

    assert result["vatRegime"] == "franchise"
    assert route.calls.last.request.method == "PATCH"


@respx.mock
def test_companies_add_milestone() -> None:
    route = respx.post(f"{BASE}/v1/companies/comp_x/milestones").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "company_milestone",
                "milestone": "first_invoice_sent",
                "reachedAt": "2026-05-20T12:00:00.000Z",
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.companies.add_milestone("comp_x", "first_invoice_sent")

    assert result["milestone"] == "first_invoice_sent"
    body = route.calls.last.request.read().decode()
    assert "first_invoice_sent" in body


# ─── invoices — backfilled portal link ────────────────────────────────


@respx.mock
def test_invoices_create_portal_link() -> None:
    respx.post(f"{BASE}/v1/invoices/inv_x/portal-link").mock(
        return_value=httpx.Response(
            200,
            json={
                "url": "https://facturino.com/portal/inv_x?token=plt_secret",
                "token": "plt_secret",
                "expires_at": "2026-05-21T12:00:00.000Z",
            },
        )
    )

    client = facturino.Client("fac_test_abc")
    result = client.invoices.create_portal_link("inv_x")
    assert "/portal/" in result["url"]


# ─── async parity ─────────────────────────────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_async_account_schedule_deletion() -> None:
    respx.post(f"{BASE}/v1/account/schedule-deletion").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "account_deletion",
                "deletionScheduledAt": "2026-06-19T00:00:00.000Z",
                "message": "Scheduled.",
            },
        )
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.account.schedule_deletion()
    assert result["deletionScheduledAt"].startswith("2026-")


@respx.mock
@pytest.mark.asyncio
async def test_async_companies_create() -> None:
    respx.post(f"{BASE}/v1/companies").mock(
        return_value=httpx.Response(200, json={"id": "comp_async"})
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.companies.create(name="async cab", siret="44306184100047")
    assert result["id"] == "comp_async"


@respx.mock
@pytest.mark.asyncio
async def test_async_invoices_portal_link() -> None:
    respx.post(f"{BASE}/v1/invoices/inv_x/portal-link").mock(
        return_value=httpx.Response(
            200, json={"url": "https://x/portal/y", "token": "t", "expires_at": "x"}
        )
    )
    async with facturino.AsyncClient("fac_test_abc") as client:
        result = await client.invoices.create_portal_link("inv_x")
    assert "portal" in result["url"]
