"""Validate resource — /v1/validate

Synchronous structural validation of business identifiers (SIRET, VAT
number, IBAN, BIC) and document payloads (invoice line items against
EN16931 / CIUS-FR Schematron rules). Useful client-side to surface
errors before hitting the write endpoints — Validate calls never mutate
any resource.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Validate:
    """Synchronous validate resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def run(self, **params: Any) -> dict[str, Any]:
        """Run a single validation request.

        The shape depends on ``kind``:

        - ``"siret"`` / ``"vat"`` / ``"iban"`` / ``"bic"``: accept a
          ``value`` string.
        - ``"invoice"``: accepts a full invoice payload and runs
          Schematron against EN16931 + CIUS-FR.
        """
        resp = self._client.post("/v1/validate", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncValidate:
    """Asynchronous validate resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def run(self, **params: Any) -> dict[str, Any]:
        resp = await self._client.post("/v1/validate", json=params)
        return resp.json()  # type: ignore[no-any-return]
