"""Events resource — /v1/events

Webhook events: list, get, retry delivery.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage
from .._types import EventRetryResult, WebhookEvent


class Events:
    """Synchronous events resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/events", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, event_id: str) -> WebhookEvent:
        resp = self._client.get(f"/v1/events/{event_id}")
        return resp.json()  # type: ignore[no-any-return]

    def retry(self, event_id: str, endpoint_id: str | None = None) -> EventRetryResult:
        """Return a scheduling receipt; ``endpoint_id`` also replays delivered events."""
        body = {"endpointId": endpoint_id} if endpoint_id else None
        resp = self._client.post(f"/v1/events/{event_id}/retry", json=body)
        return resp.json()  # type: ignore[no-any-return]


class AsyncEvents:
    """Asynchronous events resource.

    Webhook events: list, get, retry delivery.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/events", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, event_id: str) -> WebhookEvent:
        resp = await self._client.get(f"/v1/events/{event_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def retry(self, event_id: str, endpoint_id: str | None = None) -> EventRetryResult:
        """Return a scheduling receipt; ``endpoint_id`` also replays delivered events."""
        body = {"endpointId": endpoint_id} if endpoint_id else None
        resp = await self._client.post(f"/v1/events/{event_id}/retry", json=body)
        return resp.json()  # type: ignore[no-any-return]
