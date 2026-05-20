"""Account resource — /v1/account

Account introspection: returns the authenticated user, the active
company, the current plan and the scopes attached to the API key in
use. Equivalent to Stripe's "who am I" endpoint — use it on integration
startup so callers can display the connected company and the
environment (``fac_test_`` vs ``fac_live_``).
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


class AsyncAccount:
    """Asynchronous account resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve(self) -> dict[str, Any]:
        """Return the account context (user, company, plan, livemode, scopes)
        associated with the API key used by this client.
        """
        resp = await self._client.get("/v1/account")
        return resp.json()  # type: ignore[no-any-return]
