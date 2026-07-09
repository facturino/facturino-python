"""Reporting resource — /v1/reporting

VAT and revenue reports by period (Essential, Pro ou Cabinet plans).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Reporting:
    """Synchronous reporting resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def vat(self, *, period_start: str, period_end: str) -> dict[str, Any]:
        """Get a VAT report for the given period (Essential, Pro ou Cabinet plan required).

        Args:
            period_start: ISO 8601 date (e.g. "2026-01-01").
            period_end: ISO 8601 date (e.g. "2026-03-31").

        Returns:
            Dict with ``object: "vat_report"``, ``period``, ``vatBreakdown``,
            ``totalHT``, ``totalVAT``, ``totalTTC``, ``invoiceCount``.
            Amounts are in integer centimes.
        """
        resp = self._client.get(
            "/v1/reporting/vat",
            params={"period_start": period_start, "period_end": period_end},
        )
        return resp.json()  # type: ignore[no-any-return]

    def revenue(
        self,
        *,
        period_start: str,
        period_end: str,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """Get a revenue report for the given period (Essential, Pro ou Cabinet plan required).

        Args:
            period_start: ISO 8601 date (e.g. "2026-01-01").
            period_end: ISO 8601 date (e.g. "2026-03-31").
            group_by: Optional grouping — "month" or "quarter".

        Returns:
            Dict with ``object: "revenue_report"``, ``period``, ``revenue``,
            ``payments``, ``invoice_count``, ``credit_note_count``.
            If ``group_by`` is set, includes a ``breakdown`` list.
            Amounts are in integer centimes.
        """
        params: dict[str, Any] = {
            "period_start": period_start,
            "period_end": period_end,
        }
        if group_by is not None:
            params["group_by"] = group_by
        resp = self._client.get("/v1/reporting/revenue", params=params)
        return resp.json()  # type: ignore[no-any-return]


class AsyncReporting:
    """Asynchronous reporting resource.

    VAT and revenue reports by period (Essential, Pro ou Cabinet plans).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def vat(self, *, period_start: str, period_end: str) -> dict[str, Any]:
        """Get a VAT report for the given period (Essential, Pro ou Cabinet plan required).

        Args:
            period_start: ISO 8601 date (e.g. "2026-01-01").
            period_end: ISO 8601 date (e.g. "2026-03-31").

        Returns:
            Dict with ``object: "vat_report"``, ``period``, ``vatBreakdown``,
            ``totalHT``, ``totalVAT``, ``totalTTC``, ``invoiceCount``.
            Amounts are in integer centimes.
        """
        resp = await self._client.get(
            "/v1/reporting/vat",
            params={"period_start": period_start, "period_end": period_end},
        )
        return resp.json()  # type: ignore[no-any-return]

    async def revenue(
        self,
        *,
        period_start: str,
        period_end: str,
        group_by: str | None = None,
    ) -> dict[str, Any]:
        """Get a revenue report for the given period (Essential, Pro ou Cabinet plan required).

        Args:
            period_start: ISO 8601 date (e.g. "2026-01-01").
            period_end: ISO 8601 date (e.g. "2026-03-31").
            group_by: Optional grouping — "month" or "quarter".

        Returns:
            Dict with ``object: "revenue_report"``, ``period``, ``revenue``,
            ``payments``, ``invoice_count``, ``credit_note_count``.
            If ``group_by`` is set, includes a ``breakdown`` list.
            Amounts are in integer centimes.
        """
        params: dict[str, Any] = {
            "period_start": period_start,
            "period_end": period_end,
        }
        if group_by is not None:
            params["group_by"] = group_by
        resp = await self._client.get("/v1/reporting/revenue", params=params)
        return resp.json()  # type: ignore[no-any-return]
