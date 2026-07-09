"""E-reporting resource — /v1/ereporting

Create, list, get, and submit e-reporting declarations.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Ereporting:
    """Synchronous e-reporting resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/ereporting/declarations", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, declaration_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/ereporting/declarations/{declaration_id}")
        return resp.json()  # type: ignore[no-any-return]

    def create_declaration(self, **params: Any) -> dict[str, Any]:
        """Create a new e-reporting declaration.

        Args:
            type: Declaration type (b2c, international, intra_eu, payment).
            period: Period string (e.g. "2026-01").
            lines: List of reporting lines with category, amount, vatRate, vatAmount
                   (all in integer centimes / centipercent).
        """
        body = dict(params)
        for line in body.get("lines", []):
            if "vat_rate" in line and "vatRate" not in line:
                line["vatRate"] = line.pop("vat_rate")
            if "vat_amount" in line and "vatAmount" not in line:
                line["vatAmount"] = line.pop("vat_amount")
        resp = self._client.post("/v1/ereporting/declarations", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def submit_declaration(self, declaration_id: str) -> dict[str, Any]:
        """Submit a draft declaration to the PA.

        Acquires a distributed lock to prevent concurrent submissions.
        """
        resp = self._client.post(f"/v1/ereporting/declarations/{declaration_id}/submit")
        return resp.json()  # type: ignore[no-any-return]


class AsyncEreporting:
    """Asynchronous e-reporting resource.

    Create, list, get, and submit e-reporting declarations.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/ereporting/declarations", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, declaration_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/ereporting/declarations/{declaration_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def create_declaration(self, **params: Any) -> dict[str, Any]:
        """Create a new e-reporting declaration.

        Args:
            type: Declaration type (b2c, international, intra_eu, payment).
            period: Period string (e.g. "2026-01").
            lines: List of reporting lines with category, amount, vatRate, vatAmount
                   (all in integer centimes / centipercent).
        """
        body = dict(params)
        for line in body.get("lines", []):
            if "vat_rate" in line and "vatRate" not in line:
                line["vatRate"] = line.pop("vat_rate")
            if "vat_amount" in line and "vatAmount" not in line:
                line["vatAmount"] = line.pop("vat_amount")
        resp = await self._client.post("/v1/ereporting/declarations", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def submit_declaration(self, declaration_id: str) -> dict[str, Any]:
        """Submit a draft declaration to the PA.

        Acquires a distributed lock to prevent concurrent submissions.
        """
        resp = await self._client.post(f"/v1/ereporting/declarations/{declaration_id}/submit")
        return resp.json()  # type: ignore[no-any-return]
