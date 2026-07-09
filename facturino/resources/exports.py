"""Exports resource — /v1/exports

FEC export (Pro only) and RGPD data export.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Exports:
    """Synchronous exports resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def generate_fec(self, **params: Any) -> dict[str, Any]:
        """Generate a FEC export (async job, Pro/Cabinet plan only).

        FEC (Fichier des Ecritures Comptables) is required under art. A.47 A-1
        of the French tax code (LPF).

        Args:
            period_start: Start date (YYYY-MM-DD). Defaults to Jan 1 of current year.
            period_end: End date (YYYY-MM-DD). Defaults to Dec 31 of current year.
            send_to_accountant: Whether to email the FEC to the accountant.
            accountant_email: Accountant's email (required if send_to_accountant=True).

        Returns:
            Job object (202 Accepted) with job ID for polling.
        """
        resp = self._client.post("/v1/exports/fec", json=params)
        return resp.json()  # type: ignore[no-any-return]

    def get_fec_status(self, job_id: str) -> dict[str, Any]:
        """Returns download_url when completed."""
        resp = self._client.get(f"/v1/exports/fec/{job_id}")
        return resp.json()  # type: ignore[no-any-return]

    def get_status(self, job_id: str) -> dict[str, Any]:
        """Returns download_url when completed."""
        resp = self._client.get(f"/v1/exports/{job_id}")
        return resp.json()  # type: ignore[no-any-return]

    def export_invoices(self, **params: Any) -> dict[str, Any]:
        """Bulk export finalized invoices as ZIP (Factur-X PDF + CII XML). All plans.

        With no params, every non-draft invoice is exported.

        Args:
            period_start: Filter on issue date >= this date (YYYY-MM-DD).
            period_end: Filter on issue date <= this date (YYYY-MM-DD).
            statuses: List of lifecycle statuses to include (e.g. ["paid", "sent"]).

        Returns:
            Job object (202 Accepted) with job ID for polling.
        """
        resp = self._client.post("/v1/exports/invoices", json=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncExports:
    """Asynchronous exports resource.

    FEC export (Pro only) and RGPD data export.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def generate_fec(self, **params: Any) -> dict[str, Any]:
        """Generate a FEC export (async job, Pro/Cabinet plan only).

        FEC (Fichier des Ecritures Comptables) is required under art. A.47 A-1
        of the French tax code (LPF).

        Args:
            period_start: Start date (YYYY-MM-DD). Defaults to Jan 1 of current year.
            period_end: End date (YYYY-MM-DD). Defaults to Dec 31 of current year.
            send_to_accountant: Whether to email the FEC to the accountant.
            accountant_email: Accountant's email (required if send_to_accountant=True).
        """
        resp = await self._client.post("/v1/exports/fec", json=params)
        return resp.json()  # type: ignore[no-any-return]

    async def get_fec_status(self, job_id: str) -> dict[str, Any]:
        """Returns download_url when completed."""
        resp = await self._client.get(f"/v1/exports/fec/{job_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def get_status(self, job_id: str) -> dict[str, Any]:
        """Returns download_url when completed."""
        resp = await self._client.get(f"/v1/exports/{job_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def export_invoices(self, **params: Any) -> dict[str, Any]:
        """Bulk export finalized invoices as ZIP (Factur-X PDF + CII XML). All plans.

        With no params, every non-draft invoice is exported.

        Args:
            period_start: Filter on issue date >= this date (YYYY-MM-DD).
            period_end: Filter on issue date <= this date (YYYY-MM-DD).
            statuses: List of lifecycle statuses to include (e.g. ["paid", "sent"]).
        """
        resp = await self._client.post("/v1/exports/invoices", json=params)
        return resp.json()  # type: ignore[no-any-return]
