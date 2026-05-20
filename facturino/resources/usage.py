"""Usage resource — /v1/usage

Current-period consumption metrics for the authenticated account
(invoices issued, storage used, PA submissions, API calls). Useful for
in-app dashboards and proactive plan-upgrade nudges before a quota hit
triggers a 402 from the API.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Usage:
    """Synchronous usage resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve(self) -> dict[str, Any]:
        """Return the current usage snapshot.

        Includes plan limits and the consumption so far for each metered
        dimension; no historical data — the dashboard uses
        ``GET /v1/exports/revenue`` for trend lines.
        """
        resp = self._client.get("/v1/usage")
        return resp.json()  # type: ignore[no-any-return]


class AsyncUsage:
    """Asynchronous usage resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve(self) -> dict[str, Any]:
        resp = await self._client.get("/v1/usage")
        return resp.json()  # type: ignore[no-any-return]
