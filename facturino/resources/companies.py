"""Companies resource — /v1/companies

Get, update, CGV upload, Stripe Connect management.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Companies:
    """Synchronous companies resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self) -> dict[str, Any]:
        resp = self._client.get("/v1/companies")
        return resp.json()  # type: ignore[no-any-return]

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a new company under the authenticated user.

        Subject to the per-plan company quota (free / essential: 1,
        pro: 3, cabinet_*: 50+); exceeding the quota returns a 402
        ``plan_limit_error``.
        """
        resp = self._client.post("/v1/companies", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def get(self, company_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/companies/{company_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(f"/v1/companies/{company_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def update_invoicing_settings(self, company_id: str, **params: Any) -> dict[str, Any]:
        """Update the invoicing settings (numbering format, default
        payment terms, default VAT rate, footer mentions…) and the
        VAT regime for the company.
        """
        resp = self._client.patch(
            f"/v1/companies/{company_id}/invoicing-settings", json=params
        )
        return resp.json()  # type: ignore[no-any-return]

    def add_milestone(self, company_id: str, milestone: str) -> dict[str, Any]:
        """Mark an onboarding milestone as reached.

        Used by the dashboard to compute the onboarding progress and
        surface remaining steps (e.g. ``first_invoice_sent``,
        ``pa_connected``, ``bank_added``).
        """
        resp = self._client.post(
            f"/v1/companies/{company_id}/milestones", json={"milestone": milestone}
        )
        return resp.json()  # type: ignore[no-any-return]

    def upload_cgv(self, company_id: str, content: str) -> dict[str, Any]:
        """Upload CGV (terms and conditions) as base64-encoded PDF (max 5 MB)."""
        resp = self._client.post(f"/v1/companies/{company_id}/cgv", json={"content": content})
        return resp.json()  # type: ignore[no-any-return]

    def get_cgv(self, company_id: str) -> dict[str, Any]:
        """Get a signed CGV download URL (24h expiry)."""
        resp = self._client.get(f"/v1/companies/{company_id}/cgv")
        return resp.json()  # type: ignore[no-any-return]

    def delete_cgv(self, company_id: str) -> dict[str, Any]:
        resp = self._client.delete(f"/v1/companies/{company_id}/cgv")
        return resp.json()  # type: ignore[no-any-return]

    # --- PA Connection (BYOPA) ---

    def connect_pa(self, company_id: str, **params: Any) -> dict[str, Any]:
        """Connect a PA — the client provides their own PA account credentials."""
        resp = self._client.post(f"/v1/companies/{company_id}/pa-connection", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def disconnect_pa(self, company_id: str) -> dict[str, Any]:
        """Disconnect the PA from a company."""
        resp = self._client.delete(f"/v1/companies/{company_id}/pa-connection")
        return resp.json()  # type: ignore[no-any-return]

    def test_pa_connection(self, company_id: str) -> dict[str, Any]:
        """Test the PA connection (health check + credential validation)."""
        resp = self._client.post(f"/v1/companies/{company_id}/pa-connection/test", json={})
        return resp.json()  # type: ignore[no-any-return]

    # --- Stripe Connect ---

    def connect_stripe(self, **params: Any) -> dict[str, Any]:
        """Initiate Stripe Connect onboarding.

        Returns:
            A dict with the Stripe Connect account link URL.
        """
        resp = self._client.post("/v1/companies/stripe-connect", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_stripe_dashboard(self) -> dict[str, Any]:
        """Get a Stripe Express dashboard login link.

        Returns:
            A dict with the Stripe dashboard URL.
        """
        resp = self._client.get("/v1/companies/stripe-dashboard")
        return resp.json()  # type: ignore[no-any-return]

    def disconnect_stripe(self) -> dict[str, Any]:
        """Disconnect the Stripe Connect account."""
        resp = self._client.delete("/v1/companies/stripe-connect")
        return resp.json()  # type: ignore[no-any-return]


class AsyncCompanies:
    """Asynchronous companies resource.

    Get, update, CGV upload, Stripe Connect management.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/companies")
        return resp.json()  # type: ignore[no-any-return]

    async def create(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.post("/v1/companies", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/companies/{company_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/companies/{company_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def update_invoicing_settings(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(
            f"/v1/companies/{company_id}/invoicing-settings", json=params
        )
        return resp.json()  # type: ignore[no-any-return]

    async def add_milestone(self, company_id: str, milestone: str) -> dict[str, Any]:
        resp = await self._client.post(
            f"/v1/companies/{company_id}/milestones", json={"milestone": milestone}
        )
        return resp.json()  # type: ignore[no-any-return]

    async def upload_cgv(self, company_id: str, content: str) -> dict[str, Any]:
        """Upload CGV (terms and conditions) as base64-encoded PDF (max 5 MB)."""
        resp = await self._client.post(f"/v1/companies/{company_id}/cgv", json={"content": content})
        return resp.json()  # type: ignore[no-any-return]

    async def get_cgv(self, company_id: str) -> dict[str, Any]:
        """Get a signed CGV download URL (24h expiry)."""
        resp = await self._client.get(f"/v1/companies/{company_id}/cgv")
        return resp.json()  # type: ignore[no-any-return]

    async def delete_cgv(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.delete(f"/v1/companies/{company_id}/cgv")
        return resp.json()  # type: ignore[no-any-return]

    # --- PA Connection (BYOPA) ---

    async def connect_pa(self, company_id: str, **params: Any) -> dict[str, Any]:
        """Connect a PA — the client provides their own PA account credentials."""
        resp = await self._client.post(f"/v1/companies/{company_id}/pa-connection", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def disconnect_pa(self, company_id: str) -> dict[str, Any]:
        """Disconnect the PA from a company."""
        resp = await self._client.delete(f"/v1/companies/{company_id}/pa-connection")
        return resp.json()  # type: ignore[no-any-return]

    async def test_pa_connection(self, company_id: str) -> dict[str, Any]:
        """Test the PA connection (health check + credential validation)."""
        resp = await self._client.post(f"/v1/companies/{company_id}/pa-connection/test", json={})
        return resp.json()  # type: ignore[no-any-return]

    # --- Stripe Connect ---

    async def connect_stripe(self, **params: Any) -> dict[str, Any]:
        """Initiate Stripe Connect onboarding.

        Returns:
            A dict with the Stripe Connect account link URL.
        """
        resp = await self._client.post("/v1/companies/stripe-connect", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_stripe_dashboard(self) -> dict[str, Any]:
        """Get a Stripe Express dashboard login link.

        Returns:
            A dict with the Stripe dashboard URL.
        """
        resp = await self._client.get("/v1/companies/stripe-dashboard")
        return resp.json()  # type: ignore[no-any-return]

    async def disconnect_stripe(self) -> dict[str, Any]:
        """Disconnect the Stripe Connect account."""
        resp = await self._client.delete("/v1/companies/stripe-connect")
        return resp.json()  # type: ignore[no-any-return]
