"""Cabinets resource — /v1/cabinets

Multi-company management for chartered-accountant cabinets (plans
``cabinet_50``, ``cabinet_200``, ``cabinet_500``). A cabinet groups
managed client companies under a single billing entity and exposes
cross-company dashboards, activity feeds and branding.

Calls require a ``cabinet_*`` plan; integrations on ``pro`` and below
receive ``plan_limit_error`` on every endpoint here.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Cabinets:
    """Synchronous cabinets resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        """Paginated list of cabinets owned by the authenticated account."""
        resp = self._client.get("/v1/cabinets", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def retrieve(self, cabinet_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/cabinets/{cabinet_id}")
        return resp.json()  # type: ignore[no-any-return]

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a new cabinet — only allowed under a ``cabinet_*`` plan."""
        resp = self._client.post("/v1/cabinets", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def update_branding(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        """Update the white-label branding (logo, colors, custom domain)."""
        resp = self._client.patch(f"/v1/cabinets/{cabinet_id}/branding", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def dashboard(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        """Cross-company KPI dashboard (revenue, overdue, e-reporting status)."""
        resp = self._client.get(f"/v1/cabinets/{cabinet_id}/dashboard", params=params)
        return resp.json()  # type: ignore[no-any-return]

    def activity(self, cabinet_id: str, **params: Any) -> SyncPage:
        """Reverse-chronological activity feed across every managed company."""
        resp = self._client.get(f"/v1/cabinets/{cabinet_id}/activity", params=params)
        return SyncPage.from_response(
            resp.json(),
            fetcher=lambda **p: self.activity(cabinet_id, **p),
            original_params=params,
        )

    def billing_split(self, cabinet_id: str) -> dict[str, Any]:
        """Per-company breakdown of the active subscription invoice.

        Useful for cabinets that rebill subscription costs to their
        clients.
        """
        resp = self._client.get(f"/v1/cabinets/{cabinet_id}/billing-split")
        return resp.json()  # type: ignore[no-any-return]

    def list_companies(self, cabinet_id: str, **params: Any) -> SyncPage:
        """List the companies managed under a cabinet."""
        resp = self._client.get(f"/v1/cabinets/{cabinet_id}/companies", params=params)
        return SyncPage.from_response(
            resp.json(),
            fetcher=lambda **p: self.list_companies(cabinet_id, **p),
            original_params=params,
        )

    def add_company(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        """Attach an existing company (by SIRET or by ID) under the cabinet."""
        resp = self._client.post(f"/v1/cabinets/{cabinet_id}/companies", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def invite_member(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        """Invite a team member onto the cabinet (admin / accountant / viewer)."""
        resp = self._client.post(f"/v1/cabinets/{cabinet_id}/members", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncCabinets:
    """Asynchronous cabinets resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/cabinets", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def retrieve(self, cabinet_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/cabinets/{cabinet_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def create(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.post("/v1/cabinets", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def update_branding(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/cabinets/{cabinet_id}/branding", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def dashboard(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/cabinets/{cabinet_id}/dashboard", params=params)
        return resp.json()  # type: ignore[no-any-return]

    async def activity(self, cabinet_id: str, **params: Any) -> AsyncPage:
        resp = await self._client.get(f"/v1/cabinets/{cabinet_id}/activity", params=params)

        async def _fetcher(**p: Any) -> AsyncPage:
            return await self.activity(cabinet_id, **p)

        return AsyncPage.from_response(resp.json(), fetcher=_fetcher, original_params=params)

    async def billing_split(self, cabinet_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/cabinets/{cabinet_id}/billing-split")
        return resp.json()  # type: ignore[no-any-return]

    async def list_companies(self, cabinet_id: str, **params: Any) -> AsyncPage:
        resp = await self._client.get(f"/v1/cabinets/{cabinet_id}/companies", params=params)

        async def _fetcher(**p: Any) -> AsyncPage:
            return await self.list_companies(cabinet_id, **p)

        return AsyncPage.from_response(resp.json(), fetcher=_fetcher, original_params=params)

    async def add_company(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/cabinets/{cabinet_id}/companies", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def invite_member(self, cabinet_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/cabinets/{cabinet_id}/members", json=params)
        return resp.json()  # type: ignore[no-any-return]
