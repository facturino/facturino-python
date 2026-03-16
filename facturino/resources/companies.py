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

    def get(self, company_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/companies/{company_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(f"/v1/companies/{company_id}", json=params)
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


class AsyncCompanies:
    """Asynchronous companies resource.

    Get, update, CGV upload, Stripe Connect management.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/companies")
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/companies/{company_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/companies/{company_id}", json=params)
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
