"""Tests for the seven resources added in the 100% API coverage pass:
``billing``, ``cabinets``, ``notifications``, ``reference``, ``settings``,
``usage`` and ``validate``.

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
def test_billing_update_subscription_maps_snake_to_camel() -> None:
    """``cancel_at_period_end`` must be sent as ``cancelAtPeriodEnd``."""
    route = respx.patch(f"{BASE}/v1/billing/subscription").mock(
        return_value=httpx.Response(200, json={"object": "subscription"})
    )

    client = facturino.Client("fac_test_abc")
    client.billing.update_subscription(cancel_at_period_end=True)

    assert route.called
    sent_body = route.calls.last.request.read().decode()
    assert "cancelAtPeriodEnd" in sent_body
    assert "cancel_at_period_end" not in sent_body


@respx.mock
def test_billing_checkout_maps_urls_to_camel() -> None:
    route = respx.post(f"{BASE}/v1/billing/checkout").mock(
        return_value=httpx.Response(200, json={"url": "https://checkout.stripe.com/x"})
    )

    client = facturino.Client("fac_test_abc")
    client.billing.checkout(
        plan="pro",
        cycle="monthly",
        success_url="https://app.example.com/ok",
        cancel_url="https://app.example.com/no",
    )

    body = route.calls.last.request.read().decode()
    assert "successUrl" in body and "cancelUrl" in body
    assert "success_url" not in body and "cancel_url" not in body


@respx.mock
def test_billing_portal_maps_return_url() -> None:
    route = respx.post(f"{BASE}/v1/billing/portal").mock(
        return_value=httpx.Response(200, json={"url": "https://billing.stripe.com/x"})
    )

    client = facturino.Client("fac_test_abc")
    client.billing.portal(return_url="https://app.example.com/back")

    body = route.calls.last.request.read().decode()
    assert "returnUrl" in body
    assert "return_url" not in body


@respx.mock
def test_billing_pause_and_resume() -> None:
    respx.post(f"{BASE}/v1/billing/pause").mock(
        return_value=httpx.Response(200, json={"status": "paused"})
    )
    respx.post(f"{BASE}/v1/billing/resume").mock(
        return_value=httpx.Response(200, json={"status": "active"})
    )

    client = facturino.Client("fac_test_abc")
    assert client.billing.pause()["status"] == "paused"
    assert client.billing.resume()["status"] == "active"


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


# ─── notifications ────────────────────────────────────────────────────


@respx.mock
def test_notifications_list_and_mark_read() -> None:
    respx.get(f"{BASE}/v1/notifications").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "notif_1"}], "has_more": False})
    )
    respx.patch(f"{BASE}/v1/notifications/notif_1").mock(
        return_value=httpx.Response(200, json={"id": "notif_1", "read": True})
    )
    respx.patch(f"{BASE}/v1/notifications/mark-all-read").mock(
        return_value=httpx.Response(200, json={"object": "notification_batch", "updated": 7})
    )

    client = facturino.Client("fac_test_abc")
    listed = client.notifications.list(unread=True)
    assert listed.data[0]["id"] == "notif_1"

    assert client.notifications.mark_read("notif_1")["read"] is True
    assert client.notifications.mark_all_read()["updated"] == 7


@respx.mock
def test_notifications_retrieve_preferences() -> None:
    respx.get(f"{BASE}/v1/notification-preferences").mock(
        return_value=httpx.Response(200, json={"object": "notification_preferences"})
    )

    client = facturino.Client("fac_test_abc")
    result = client.notifications.retrieve_preferences()
    assert result["object"] == "notification_preferences"


@respx.mock
def test_notifications_update_preferences_sends_full_body() -> None:
    route = respx.patch(f"{BASE}/v1/notification-preferences").mock(
        return_value=httpx.Response(200, json={"object": "notification_preferences"})
    )

    client = facturino.Client("fac_test_abc")
    client.notifications.update_preferences(
        preferences={"invoice_paid": {"email": False, "inApp": True, "push": True}}
    )

    body = route.calls.last.request.read().decode()
    assert "invoice_paid" in body
    assert "inApp" in body


# ─── settings ─────────────────────────────────────────────────────────


@respx.mock
def test_settings_accounting_round_trip() -> None:
    respx.get(f"{BASE}/v1/companies/comp_x/settings/accounting").mock(
        return_value=httpx.Response(200, json={"vatRegime": "normal"})
    )
    respx.patch(f"{BASE}/v1/companies/comp_x/settings/accounting").mock(
        return_value=httpx.Response(200, json={"vatRegime": "franchise"})
    )

    client = facturino.Client("fac_test_abc")
    assert client.settings.retrieve_accounting("comp_x")["vatRegime"] == "normal"
    assert (
        client.settings.update_accounting("comp_x", vatRegime="franchise")["vatRegime"]
        == "franchise"
    )


@respx.mock
def test_settings_reminders_round_trip() -> None:
    respx.get(f"{BASE}/v1/companies/comp_x/settings/reminders").mock(
        return_value=httpx.Response(200, json={"enabled": True, "schedule": [7, 15, 30]})
    )
    respx.patch(f"{BASE}/v1/companies/comp_x/settings/reminders").mock(
        return_value=httpx.Response(200, json={"enabled": False})
    )

    client = facturino.Client("fac_test_abc")
    assert client.settings.retrieve_reminders("comp_x")["schedule"] == [7, 15, 30]
    assert client.settings.update_reminders("comp_x", enabled=False)["enabled"] is False


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


# ─── cabinets ─────────────────────────────────────────────────────────


@respx.mock
def test_cabinets_full_surface() -> None:
    respx.get(f"{BASE}/v1/cabinets").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "cab_1"}], "has_more": False})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_1").mock(
        return_value=httpx.Response(200, json={"id": "cab_1", "plan": "cabinet_50"})
    )
    respx.post(f"{BASE}/v1/cabinets").mock(
        return_value=httpx.Response(200, json={"id": "cab_new"})
    )
    respx.patch(f"{BASE}/v1/cabinets/cab_1/branding").mock(
        return_value=httpx.Response(200, json={"id": "cab_1", "branding": {"primaryColor": "#FF6D00"}})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_1/dashboard").mock(
        return_value=httpx.Response(200, json={"totalRevenue": "12345.67"})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_1/activity").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_1/billing-split").mock(
        return_value=httpx.Response(200, json={"split": []})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_1/companies").mock(
        return_value=httpx.Response(200, json={"data": [], "has_more": False})
    )
    respx.post(f"{BASE}/v1/cabinets/cab_1/companies").mock(
        return_value=httpx.Response(200, json={"id": "comp_added"})
    )
    respx.post(f"{BASE}/v1/cabinets/cab_1/members").mock(
        return_value=httpx.Response(200, json={"id": "mem_pending", "status": "invited"})
    )

    client = facturino.Client("fac_test_abc")
    assert client.cabinets.list().data[0]["id"] == "cab_1"
    assert client.cabinets.retrieve("cab_1")["plan"] == "cabinet_50"
    assert client.cabinets.create(name="Mon cabinet", plan="cabinet_50")["id"] == "cab_new"
    assert client.cabinets.update_branding("cab_1", primaryColor="#FF6D00")["branding"][
        "primaryColor"
    ] == "#FF6D00"
    assert client.cabinets.dashboard("cab_1")["totalRevenue"] == "12345.67"
    assert client.cabinets.activity("cab_1").data == []
    assert client.cabinets.billing_split("cab_1")["split"] == []
    assert client.cabinets.list_companies("cab_1").data == []
    assert client.cabinets.add_company("cab_1", siret="44306184100047")["id"] == "comp_added"
    invited = client.cabinets.invite_member("cab_1", email="test@example.com", role="accountant")
    assert invited["status"] == "invited"


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
async def test_async_cabinets_create_and_dashboard() -> None:
    respx.post(f"{BASE}/v1/cabinets").mock(
        return_value=httpx.Response(200, json={"id": "cab_async"})
    )
    respx.get(f"{BASE}/v1/cabinets/cab_async/dashboard").mock(
        return_value=httpx.Response(200, json={"totalRevenue": "99.00"})
    )

    async with facturino.AsyncClient("fac_test_abc") as client:
        cab = await client.cabinets.create(name="async cab", plan="cabinet_50")
        dash = await client.cabinets.dashboard(cab["id"])

    assert cab["id"] == "cab_async"
    assert dash["totalRevenue"] == "99.00"


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
