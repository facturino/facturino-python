"""Account resource — /v1/account

Account introspection (the authenticated user, active company, plan and
key scopes) plus the RGPD data-export endpoints (article 20): request a
full export and download it once prepared.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Account:
    """Synchronous account resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve(self) -> dict[str, Any]:
        """Return the account context (user, company, plan, livemode, scopes)
        associated with the API key used by this client.
        """
        resp = self._client.get("/v1/account")
        return resp.json()  # type: ignore[no-any-return]

    def request_export(self) -> dict[str, Any]:
        """Request a full data export (RGPD art. 20).

        The export is prepared synchronously and returned as
        ``{"object": "export", "id": ..., "expires_at": ...}``. Pass the
        ``id`` to :meth:`download_export` for a short-lived signed URL.
        """
        resp = self._client.post("/v1/account/export")
        return resp.json()  # type: ignore[no-any-return]

    def download_export(self, export_id: str) -> dict[str, Any]:
        """Return a short-lived (5 min) signed URL for a prepared export."""
        resp = self._client.get(f"/v1/account/exports/{export_id}/download")
        return resp.json()  # type: ignore[no-any-return]


class AsyncAccount:
    """Asynchronous account resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/account")
        return resp.json()  # type: ignore[no-any-return]

    async def request_export(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/account/export")
        return resp.json()  # type: ignore[no-any-return]

    async def download_export(self, export_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/account/exports/{export_id}/download")
        return resp.json()  # type: ignore[no-any-return]
