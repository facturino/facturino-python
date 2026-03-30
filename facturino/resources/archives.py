"""Archives resource — /v1/archives

Read-only access to archived invoices (hash-chain verified).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Archives:
    """Synchronous archives resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        """List archived invoices."""
        resp = self._client.get("/v1/archives", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, invoice_id: str) -> dict[str, Any]:
        """Get an archived invoice by its original invoice ID.

        Args:
            invoice_id: The original invoice ID.

        Returns:
            The archive entry dict (includes hash chain data).
        """
        resp = self._client.get(f"/v1/archives/{invoice_id}")
        return resp.json()  # type: ignore[no-any-return]


class AsyncArchives:
    """Asynchronous archives resource.

    Read-only access to archived invoices (hash-chain verified).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        """List archived invoices."""
        resp = await self._client.get("/v1/archives", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, invoice_id: str) -> dict[str, Any]:
        """Get an archived invoice by its original invoice ID.

        Args:
            invoice_id: The original invoice ID.

        Returns:
            The archive entry dict (includes hash chain data).
        """
        resp = await self._client.get(f"/v1/archives/{invoice_id}")
        return resp.json()  # type: ignore[no-any-return]
