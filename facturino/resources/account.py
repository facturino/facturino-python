"""Account resource — /v1/account

Account introspection (the authenticated user, active company, plan and
key scopes) plus the RGPD lifecycle endpoints:

- schedule / cancel an account deletion (article 17),
- request / download a full data export (article 20),
- update per-channel email-notification preferences.
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

    def schedule_deletion(self) -> dict[str, Any]:
        """Schedule the authenticated account for deletion in 30 days (RGPD art. 17).

        Returns 409 if a deletion is already scheduled, and 400 while
        the account still has an active paid subscription. The
        deletion is reversible during the grace period — call
        :meth:`cancel_deletion` to abort.
        """
        resp = self._client.post("/v1/account/schedule-deletion")
        return resp.json()  # type: ignore[no-any-return]

    def cancel_deletion(self) -> dict[str, Any]:
        """Cancel a pending account deletion (within the 30-day grace window)."""
        resp = self._client.post("/v1/account/cancel-deletion")
        return resp.json()  # type: ignore[no-any-return]

    def request_export(self) -> dict[str, Any]:
        """Request a full data export (RGPD art. 20).

        Returns immediately with an ``exportId``; the file is prepared
        asynchronously and the user receives an in-app notification
        when ready. Pass the returned id to :meth:`download_export`
        to retrieve a short-lived signed URL.
        """
        resp = self._client.post("/v1/account/export")
        return resp.json()  # type: ignore[no-any-return]

    def download_export(self, export_id: str) -> dict[str, Any]:
        """Return a short-lived (5 min) signed URL for a prepared export."""
        resp = self._client.get(f"/v1/account/exports/{export_id}/download")
        return resp.json()  # type: ignore[no-any-return]

    def update_notifications(self, **params: Any) -> dict[str, Any]:
        """Update the per-channel email-notification preferences.

        This endpoint manages broadcast preferences (which transactional
        emails the user wants to receive); per-event channel
        preferences live under
        :meth:`facturino.resources.notifications.Notifications.update_preferences`
        instead.
        """
        resp = self._client.patch("/v1/account/notifications", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncAccount:
    """Asynchronous account resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/account")
        return resp.json()  # type: ignore[no-any-return]

    async def schedule_deletion(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/account/schedule-deletion")
        return resp.json()  # type: ignore[no-any-return]

    async def cancel_deletion(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/account/cancel-deletion")
        return resp.json()  # type: ignore[no-any-return]

    async def request_export(self) -> dict[str, Any]:
        resp = await self._client.post("/v1/account/export")
        return resp.json()  # type: ignore[no-any-return]

    async def download_export(self, export_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/account/exports/{export_id}/download")
        return resp.json()  # type: ignore[no-any-return]

    async def update_notifications(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch("/v1/account/notifications", json=params)
        return resp.json()  # type: ignore[no-any-return]
