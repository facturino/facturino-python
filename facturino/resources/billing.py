"""Billing resource — /v1/billing

Manage the Stripe-backed subscription, list and download platform
invoices, and open Customer-Portal / Checkout sessions.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Billing:
    """Synchronous billing resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve_subscription(self) -> dict[str, Any]:
        """Current subscription (plan, cycle, status, period bounds)."""
        resp = self._client.get("/v1/billing/subscription")
        return resp.json()  # type: ignore[no-any-return]

    def update_subscription(self, **params: Any) -> dict[str, Any]:
        """Change plan, cycle or cancel-at-period-end.

        Args:
            plan: ``"essential"``, ``"pro"`` or one of the cabinet plans.
            cycle: ``"monthly"`` or ``"annual"``.
            cancel_at_period_end / cancelAtPeriodEnd: when ``True``, the
                subscription stays active until the end of the current
                period and is then cancelled automatically.
        """
        body = dict(params)
        if "cancel_at_period_end" in body and "cancelAtPeriodEnd" not in body:
            body["cancelAtPeriodEnd"] = body.pop("cancel_at_period_end")
        resp = self._client.patch("/v1/billing/subscription", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def checkout(self, **params: Any) -> dict[str, Any]:
        """Create a Stripe Checkout session for the first paid subscription.

        Args:
            plan: target plan.
            cycle: ``"monthly"`` or ``"annual"``.
            success_url / successUrl: Stripe redirect after success.
            cancel_url / cancelUrl: Stripe redirect on abort.
        """
        body = dict(params)
        if "success_url" in body and "successUrl" not in body:
            body["successUrl"] = body.pop("success_url")
        if "cancel_url" in body and "cancelUrl" not in body:
            body["cancelUrl"] = body.pop("cancel_url")
        resp = self._client.post("/v1/billing/checkout", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def portal(self, **params: Any) -> dict[str, Any]:
        """Create a Stripe Customer Portal session for self-service changes."""
        body = dict(params)
        if "return_url" in body and "returnUrl" not in body:
            body["returnUrl"] = body.pop("return_url")
        resp = self._client.post("/v1/billing/portal", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def pause(self) -> dict[str, Any]:
        """Pause the active subscription (Pro+ plans)."""
        resp = self._client.post("/v1/billing/pause")
        return resp.json()  # type: ignore[no-any-return]

    def resume(self) -> dict[str, Any]:
        """Resume a paused subscription."""
        resp = self._client.post("/v1/billing/resume")
        return resp.json()  # type: ignore[no-any-return]

    def list_invoices(self, **params: Any) -> dict[str, Any]:
        """Paginated list of platform invoices issued to this account."""
        resp = self._client.get("/v1/billing/invoices", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_invoice_pdf(self, invoice_id: str) -> dict[str, Any]:
        """Return a short-lived signed URL to download the PDF."""
        resp = self._client.get(f"/v1/billing/invoices/{invoice_id}/pdf")
        return resp.json()  # type: ignore[no-any-return]


class AsyncBilling:
    """Asynchronous billing resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve_subscription(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/billing/subscription")
        return resp.json()  # type: ignore[no-any-return]

    async def update_subscription(self, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "cancel_at_period_end" in body and "cancelAtPeriodEnd" not in body:
            body["cancelAtPeriodEnd"] = body.pop("cancel_at_period_end")
        resp = await self._client.patch("/v1/billing/subscription", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def checkout(self, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "success_url" in body and "successUrl" not in body:
            body["successUrl"] = body.pop("success_url")
        if "cancel_url" in body and "cancelUrl" not in body:
            body["cancelUrl"] = body.pop("cancel_url")
        resp = await self._client.post("/v1/billing/checkout", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def portal(self, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "return_url" in body and "returnUrl" not in body:
            body["returnUrl"] = body.pop("return_url")
        resp = await self._client.post("/v1/billing/portal", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def pause(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/billing/pause")
        return resp.json()  # type: ignore[no-any-return]

    async def resume(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/billing/resume")
        return resp.json()  # type: ignore[no-any-return]

    async def list_invoices(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.get("/v1/billing/invoices", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_invoice_pdf(self, invoice_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/billing/invoices/{invoice_id}/pdf")
        return resp.json()  # type: ignore[no-any-return]
