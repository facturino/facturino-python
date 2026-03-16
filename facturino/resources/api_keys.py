"""API keys resource — /v1/api-keys

Create, list, revoke, and roll API keys.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class ApiKeys:
    """Synchronous API keys resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a new API key.

        The full key value is only returned at creation time. Store it
        securely -- it cannot be retrieved later.

        Args:
            name: Human-readable name for the key.
            permissions: List of permission scopes.
        """
        resp = self._client.post("/v1/api-keys", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def list(self) -> dict[str, Any]:
        resp = self._client.get("/v1/api-keys")
        return resp.json()  # type: ignore[no-any-return]

    def get(self, key_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/api-keys/{key_id}")
        return resp.json()  # type: ignore[no-any-return]

    def revoke(self, key_id: str) -> None:
        """Immediate and irreversible."""
        self._client.delete(f"/v1/api-keys/{key_id}")

    def roll(self, key_id: str) -> dict[str, Any]:
        """Revoke the old key and create a new one atomically.

        The response includes the full new key value.
        """
        resp = self._client.post(f"/v1/api-keys/{key_id}/roll")
        return resp.json()  # type: ignore[no-any-return]


class AsyncApiKeys:
    """Asynchronous API keys resource.

    Create, list, revoke, and roll API keys.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a new API key.

        The full key value is only returned at creation time. Store it
        securely -- it cannot be retrieved later.

        Args:
            name: Human-readable name for the key.
            permissions: List of permission scopes.
        """
        resp = await self._client.post("/v1/api-keys", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/api-keys")
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, key_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/api-keys/{key_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def revoke(self, key_id: str) -> None:
        """Immediate and irreversible."""
        await self._client.delete(f"/v1/api-keys/{key_id}")

    async def roll(self, key_id: str) -> dict[str, Any]:
        """Revoke the old key and create a new one atomically.

        The response includes the full new key value.
        """
        resp = await self._client.post(f"/v1/api-keys/{key_id}/roll")
        return resp.json()  # type: ignore[no-any-return]
