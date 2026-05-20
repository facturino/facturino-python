"""Settings resource — /v1/companies/{companyId}/settings

Per-company configuration that does not belong to a single resource:
accounting accounts (FEC mapping) and the automatic reminder schedule.
Every method takes the target ``company_id`` as its first argument so a
single API key can administer settings on each of the companies it is
scoped to.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Settings:
    """Synchronous settings resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def retrieve_accounting(self, company_id: str) -> dict[str, Any]:
        """Accounting configuration (FEC accounts, journal codes, VAT regime)."""
        resp = self._client.get(f"/v1/companies/{company_id}/settings/accounting")
        return resp.json()  # type: ignore[no-any-return]

    def update_accounting(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(
            f"/v1/companies/{company_id}/settings/accounting", json=params
        )
        return resp.json()  # type: ignore[no-any-return]

    def retrieve_reminders(self, company_id: str) -> dict[str, Any]:
        """Automatic dunning reminder schedule (J+7 / J+15 / J+30 by default)."""
        resp = self._client.get(f"/v1/companies/{company_id}/settings/reminders")
        return resp.json()  # type: ignore[no-any-return]

    def update_reminders(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(
            f"/v1/companies/{company_id}/settings/reminders", json=params
        )
        return resp.json()  # type: ignore[no-any-return]


class AsyncSettings:
    """Asynchronous settings resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def retrieve_accounting(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/companies/{company_id}/settings/accounting")
        return resp.json()  # type: ignore[no-any-return]

    async def update_accounting(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(
            f"/v1/companies/{company_id}/settings/accounting", json=params
        )
        return resp.json()  # type: ignore[no-any-return]

    async def retrieve_reminders(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/companies/{company_id}/settings/reminders")
        return resp.json()  # type: ignore[no-any-return]

    async def update_reminders(self, company_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(
            f"/v1/companies/{company_id}/settings/reminders", json=params
        )
        return resp.json()  # type: ignore[no-any-return]
