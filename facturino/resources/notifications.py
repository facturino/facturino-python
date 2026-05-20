"""Notifications resource — /v1/notifications & /v1/notification-preferences

In-app notification feed for the authenticated user (paginated list,
mark single / all read) and per-event notification preferences
(email / push / in-app). The feed lives under ``/v1/notifications`` and
mirrors the dashboard "bell" icon; per-event preferences are stored at
the user level under ``/v1/notification-preferences`` and override the
channel-matrix defaults from the API reference.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Notifications:
    """Synchronous notifications resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        """Paginated list of notifications for the authenticated user.

        Args:
            limit: max items per page (default 25, max 100).
            starting_after / ending_before: cursor pagination.
            unread: when ``True``, filter on unread only.
        """
        resp = self._client.get("/v1/notifications", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def mark_read(self, notification_id: str) -> dict[str, Any]:
        """Mark a single notification as read."""
        resp = self._client.patch(f"/v1/notifications/{notification_id}", json={"read": True})
        return resp.json()  # type: ignore[no-any-return]

    def mark_all_read(self) -> dict[str, Any]:
        """Mark every unread notification as read."""
        resp = self._client.patch("/v1/notifications/mark-all-read", json={})
        return resp.json()  # type: ignore[no-any-return]

    def retrieve_preferences(self) -> dict[str, Any]:
        """Retrieve the per-event notification preferences for the user."""
        resp = self._client.get("/v1/notification-preferences")
        return resp.json()  # type: ignore[no-any-return]

    def update_preferences(self, **params: Any) -> dict[str, Any]:
        """Update per-event notification preferences.

        The body merges with the existing preferences map; pass for
        example ``preferences={"invoice_paid": {"email": False,
        "inApp": True, "push": True}}`` to override a single event.
        """
        resp = self._client.patch("/v1/notification-preferences", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncNotifications:
    """Asynchronous notifications resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/notifications", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def mark_read(self, notification_id: str) -> dict[str, Any]:
        resp = await self._client.patch(
            f"/v1/notifications/{notification_id}", json={"read": True}
        )
        return resp.json()  # type: ignore[no-any-return]

    async def mark_all_read(self) -> dict[str, Any]:
        resp = await self._client.patch("/v1/notifications/mark-all-read", json={})
        return resp.json()  # type: ignore[no-any-return]

    async def retrieve_preferences(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/notification-preferences")
        return resp.json()  # type: ignore[no-any-return]

    async def update_preferences(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch("/v1/notification-preferences", json=params)
        return resp.json()  # type: ignore[no-any-return]
