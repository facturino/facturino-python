"""Billing resource — /v1/billing

Manage the Stripe-backed subscription, list and download platform
invoices, and open Customer-Portal / Checkout sessions.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


def _normalize_plan_id(params: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``params`` with ``plan`` / ``plan_id`` renamed to ``planId``."""
    body = dict(params)
    if "plan" in body and "planId" not in body:
        body["planId"] = body.pop("plan")
    if "plan_id" in body and "planId" not in body:
        body["planId"] = body.pop("plan_id")
    return body


def _apply_cycle_to_annual(body: dict[str, Any]) -> None:
    """Convert the ergonomic ``cycle`` kwarg to the wire field ``annual``.

    The backend ``PATCH /v1/billing/subscription`` schema is strict and only
    accepts ``planId`` and ``annual``. An explicit ``annual`` wins; otherwise
    ``cycle`` is mapped (``"annual"`` -> ``True``) and dropped. Period-end
    cancellation is handled by the Stripe Customer Portal, so any
    ``cancel_at_period_end`` hint is dropped rather than sent.
    """
    cycle = body.pop("cycle", None)
    if "annual" not in body and cycle is not None:
        body["annual"] = cycle == "annual"
    body.pop("cancel_at_period_end", None)
    body.pop("cancelAtPeriodEnd", None)


def _checkout_body(params: dict[str, Any]) -> dict[str, Any]:
    """Build the strict ``POST /v1/billing/checkout`` body.

    Accepts both snake_case and camelCase kwargs, renames ``plan`` to
    ``planId`` and the redirect URLs to their camelCase form, and drops
    cycle/annual/cancel hints the checkout endpoint does not accept.
    """
    body = _normalize_plan_id(params)
    if "success_url" in body and "successUrl" not in body:
        body["successUrl"] = body.pop("success_url")
    if "cancel_url" in body and "cancelUrl" not in body:
        body["cancelUrl"] = body.pop("cancel_url")
    for unsupported in ("cycle", "annual", "cancel_at_period_end", "cancelAtPeriodEnd"):
        body.pop(unsupported, None)
    return body


class Billing:
    """Synchronous billing resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve_subscription(self) -> dict[str, Any]:
        """Current subscription (plan, cycle, status, period bounds)."""
        resp = self._client.get("/v1/billing/subscription")
        return resp.json()  # type: ignore[no-any-return]

    def update_subscription(self, **params: Any) -> dict[str, Any]:
        """Change plan and/or billing cycle.

        Args:
            plan / plan_id / planId: ``"essential"`` or ``"pro"`` (sent on the
                wire as ``planId``).
            cycle: ``"monthly"`` or ``"annual"`` — converted to ``annual``
                (bool) on the wire.
            annual: ``True`` for yearly billing, ``False`` for monthly. Takes
                precedence when supplied directly.

        To cancel at the end of the current period, open the Stripe Customer
        Portal via :meth:`portal` — this endpoint does not handle cancellation.
        """
        body = _normalize_plan_id(params)
        _apply_cycle_to_annual(body)
        resp = self._client.patch("/v1/billing/subscription", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def checkout(self, **params: Any) -> dict[str, Any]:
        """Create a Stripe Checkout session for the first paid subscription.

        Required:
            plan / plan_id / planId: target plan (sent on the wire as
                ``planId``).
            success_url / successUrl: Stripe redirect after success.
            cancel_url / cancelUrl: Stripe redirect on abort.

        The billing cycle is selected inside the Stripe Checkout session, so
        ``cycle`` / ``annual`` are not accepted here and are dropped if passed.
        """
        body = _checkout_body(params)
        resp = self._client.post("/v1/billing/checkout", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def portal(self, **params: Any) -> dict[str, Any]:
        """Create a Stripe Customer Portal session for self-service changes.

        Required:
            return_url / returnUrl: where Stripe redirects when the
                customer leaves the portal.
        """
        body = dict(params)
        if "return_url" in body and "returnUrl" not in body:
            body["returnUrl"] = body.pop("return_url")
        resp = self._client.post("/v1/billing/portal", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def pause(self, months: int) -> dict[str, Any]:
        """Pause the active subscription (Pro+ plans).

        Args:
            months: Number of months to pause for (1, 2 or 3). The
                subscription resumes automatically afterwards.
        """
        resp = self._client.post("/v1/billing/pause", json={"months": months})
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
        body = _normalize_plan_id(params)
        _apply_cycle_to_annual(body)
        resp = await self._client.patch("/v1/billing/subscription", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def checkout(self, **params: Any) -> dict[str, Any]:
        body = _checkout_body(params)
        resp = await self._client.post("/v1/billing/checkout", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def portal(self, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "return_url" in body and "returnUrl" not in body:
            body["returnUrl"] = body.pop("return_url")
        resp = await self._client.post("/v1/billing/portal", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def pause(self, months: int) -> dict[str, Any]:
        resp = await self._client.post("/v1/billing/pause", json={"months": months})
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
