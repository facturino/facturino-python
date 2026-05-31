"""Health resource — /v1/health

Lightweight liveness probe for the Facturino API. Returns the service
status and the API version; useful for uptime checks and for confirming
that an API key reaches the platform before running real traffic.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Health:
    """Synchronous health resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def check(self) -> dict[str, Any]:
        """Return the current service health snapshot."""
        resp = self._client.get("/v1/health")
        return resp.json()  # type: ignore[no-any-return]


class AsyncHealth:
    """Asynchronous health resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def check(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/health")
        return resp.json()  # type: ignore[no-any-return]
