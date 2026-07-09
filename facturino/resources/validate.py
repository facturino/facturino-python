"""Validate resource — /v1/validate

Dry-run conformity check of an invoice draft against the same EN16931 /
CIUS-FR rules as ``invoices.create``, without persisting anything. Use it to
surface conformity warnings before creating an invoice. To check a customer's
SIRET/VAT, use ``customers.lookup`` (SIRENE/VIES).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Validate:
    """Synchronous validate resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def run(self, **params: Any) -> dict[str, Any]:
        """Validate an invoice payload without creating it.

        Accepts the same fields as ``invoices.create`` (``customer_id``,
        ``buyer``, ``lines``, ``dates``, ``payment``...). Returns
        ``{"valid": bool, "warnings": [...], "schemaVersion": str}``.
        """
        resp = self._client.post("/v1/validate", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncValidate:
    """Asynchronous validate resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def run(self, **params: Any) -> dict[str, Any]:
        """Validate an invoice payload without creating it.

        Accepts the same fields as ``invoices.create``. Returns
        ``{"valid": bool, "warnings": [...], "schemaVersion": str}``.
        """
        resp = await self._client.post("/v1/validate", json=params)
        return resp.json()  # type: ignore[no-any-return]
