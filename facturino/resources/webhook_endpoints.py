"""Webhook endpoints resource — /v1/webhook-endpoints

CRUD for webhook endpoint configuration.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class WebhookEndpoints:
    """Synchronous webhook endpoints resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a webhook endpoint.

        Args:
            url: The URL to receive webhook events.
            events: List of event types to subscribe to (e.g. ["invoice.created"]).
            description: Optional description.

        Returns:
            The created endpoint dict (includes the signing secret).
        """
        resp = self._client.post("/v1/webhook-endpoints", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/webhook-endpoints", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, endpoint_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/webhook-endpoints/{endpoint_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, endpoint_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(f"/v1/webhook-endpoints/{endpoint_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, endpoint_id: str) -> None:
        self._client.delete(f"/v1/webhook-endpoints/{endpoint_id}")


class AsyncWebhookEndpoints:
    """Asynchronous webhook endpoints resource.

    CRUD for webhook endpoint configuration.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a webhook endpoint.

        The response includes the signing secret, which is only shown at
        creation time.

        Args:
            url: The URL to receive webhook events.
            events: List of event types to subscribe to (e.g. ["invoice.created"]).
            description: Optional description.
        """
        resp = await self._client.post("/v1/webhook-endpoints", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/webhook-endpoints", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, endpoint_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/webhook-endpoints/{endpoint_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, endpoint_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/webhook-endpoints/{endpoint_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, endpoint_id: str) -> None:
        await self._client.delete(f"/v1/webhook-endpoints/{endpoint_id}")
