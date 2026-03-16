"""Customers resource — /v1/customers

CRUD operations, Sirene/VIES lookup, and CSV import/export.
"""

from __future__ import annotations

import builtins
from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Customers:
    """Synchronous customers resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a customer.

        Args:
            name: Company or individual name.
            type: "company" or "individual".
            email: Contact email.
            siret: 14-digit SIRET (B2B France).
            vat_number / vatNumber: EU VAT number.
            address: Address dict (line1, postalCode, city, country).
            **params: Additional fields.

        Returns:
            The created customer dict.
        """
        body = dict(params)
        if "vat_number" in body and "vatNumber" not in body:
            body["vatNumber"] = body.pop("vat_number")
        resp = self._client.post("/v1/customers", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/customers", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, customer_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/customers/{customer_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, customer_id: str, **params: Any) -> dict[str, Any]:
        resp = self._client.patch(f"/v1/customers/{customer_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, customer_id: str) -> None:
        self._client.delete(f"/v1/customers/{customer_id}")

    def lookup(self, **params: Any) -> dict[str, Any]:
        """Look up a company via the Sirene API (SIRET or name search).

        Args:
            siret: 14-digit SIRET to look up.
            query: Company name to search for.
        """
        resp = self._client.post("/v1/customers/lookup", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def import_csv(self, rows: builtins.list[dict[str, Any]]) -> dict[str, Any]:
        """Import customers from CSV rows (max 1000 rows).

        Args:
            rows: List of customer dicts to import.

        Returns:
            Job object (202 Accepted).
        """
        resp = self._client.post("/v1/customers/import", json={"rows": rows})
        return resp.json()  # type: ignore[no-any-return]

    def export_csv(self) -> dict[str, Any]:
        """Export customers as CSV (async job).

        Returns:
            Job object (202 Accepted).
        """
        resp = self._client.post("/v1/customers/export")
        return resp.json()  # type: ignore[no-any-return]


class AsyncCustomers:
    """Asynchronous customers resource.

    CRUD operations, Sirene/VIES lookup, and CSV import/export.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a customer.

        Args:
            name: Company or individual name.
            type: "company" or "individual".
            email: Contact email.
            siret: 14-digit SIRET (B2B France).
            vat_number / vatNumber: EU VAT number.
            address: Address dict (line1, postalCode, city, country).
            **params: Additional fields.
        """
        body = dict(params)
        if "vat_number" in body and "vatNumber" not in body:
            body["vatNumber"] = body.pop("vat_number")
        resp = await self._client.post("/v1/customers", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/customers", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, customer_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/customers/{customer_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, customer_id: str, **params: Any) -> dict[str, Any]:
        resp = await self._client.patch(f"/v1/customers/{customer_id}", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, customer_id: str) -> None:
        await self._client.delete(f"/v1/customers/{customer_id}")

    async def lookup(self, **params: Any) -> dict[str, Any]:
        """Look up a company via the Sirene API (SIRET or name search).

        Args:
            siret: 14-digit SIRET to look up.
            query: Company name to search for.
        """
        resp = await self._client.post("/v1/customers/lookup", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def import_csv(self, rows: builtins.list[dict[str, Any]]) -> dict[str, Any]:
        """Import customers from CSV rows (max 1000 rows).

        Returns a job object (202 Accepted).
        """
        resp = await self._client.post("/v1/customers/import", json={"rows": rows})
        return resp.json()  # type: ignore[no-any-return]

    async def export_csv(self) -> dict[str, Any]:
        """Export customers as CSV (async job).

        Returns a job object (202 Accepted).
        """
        resp = await self._client.post("/v1/customers/export")
        return resp.json()  # type: ignore[no-any-return]
