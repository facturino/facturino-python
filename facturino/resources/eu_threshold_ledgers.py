"""Annual EU threshold ledger resource — /v1/eu-threshold-ledgers

The ledger is the running total the two EU B2C thresholds are assessed on. It is
deliberately separate from the seller's fiscal profile: a profile revision is an
immutable RULE that decisions freeze, while a turnover total moves with every
sale and gets corrected. Keeping them apart is what lets a correction be
recorded without rewriting the rule a frozen decision was taken under.

It carries TWO counters, strictly apart and INDEPENDENT: the common EUR 10,000
threshold (art. 59c(1) -- intra-EU distance sales of goods AND cross-border
services to consumers) and the EUR 100,000 location-evidence threshold
(Reg. 282/2011 art. 24b, 2nd subparagraph -- electronically supplied services,
DOMESTIC ones included). A distance sale of goods raises the first and never the
second, so every figure comes in a pair -- and neither bounds the other, because
the common threshold counts only cross-border supplies. A seller whose electronic
services are mostly sold at home legitimately declares more on the second.

Nothing is assumed. Opening a year declares four figures -- the two totals and
their services part -- plus whether every covered sale goes through Facturino.
Sales made elsewhere are never assumed absent: under ``mixed_channels`` they
enter through adjustments, and the ledger serves a decision only up to the day
those channels are declared complete through.

The ledger is append-only: there is no update and no delete. Giving an amount
back is a qualified CORRECTION, which names the movement it corrects; what
cannot be qualified that way puts the ledger under review instead.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient

_PATH = "/v1/eu-threshold-ledgers"

#: snake_case aliases accepted on input, so callers stay Pythonic while the HTTP
#: payload always matches the published camelCase contract.
_FIELD_ALIASES = {
    "previous_year_amount": "previousYearAmount",
    "current_year_opening": "currentYearOpening",
    "previous_year_evidence_amount": "previousYearEvidenceAmount",
    "current_year_evidence_opening": "currentYearEvidenceOpening",
    "coverage_mode": "coverageMode",
    "external_complete_through_date": "externalCompleteThroughDate",
    "evidence_amount": "evidenceAmount",
    "corrects_entry_id": "correctsEntryId",
    "related_resource_type": "relatedResourceType",
    "related_resource_id": "relatedResourceId",
    "evidence_reference": "evidenceReference",
}


def _body(params: dict[str, Any]) -> dict[str, Any]:
    return {_FIELD_ALIASES.get(key, key): value for key, value in params.items()}


def _query(limit: int | None, starting_after: str | None) -> dict[str, Any]:
    """Cursor pagination, sent only when asked for."""
    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if starting_after is not None:
        params["starting_after"] = starting_after
    return params


class EuThresholdLedgers:
    """Synchronous EU threshold ledger resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def open(self, **params: Any) -> dict[str, Any]:
        """Open a calendar year.

        Args:
            year: Four-digit calendar year.
            previous_year_amount: Covered turnover of the PREVIOUS calendar
                year, VAT excluded, in integer cents.
            current_year_opening: Covered turnover ALREADY made this year, VAT
                excluded, in integer cents.
            previous_year_evidence_amount: The art. 24b perimeter for the same
                period -- every service supplied electronically to a consumer of
                the Union, DOMESTIC ones included. INDEPENDENT of
                ``previous_year_amount`` in both directions.
            current_year_evidence_opening: The matching figure for the current
                year. Independent for the same reason.
            coverage_mode: ``"facturino_only"`` -- a DECLARATION that every
                covered sale goes through Facturino -- or ``"mixed_channels"``.
            external_complete_through_date: Day the channels other than
                Facturino are complete through. It must belong to the ledger's
                own year and must never be in the future.

        A year already open is never rewritten (``eu_threshold_year_already_open``):
        decisions were frozen on its opening figures.
        """
        resp = self._client.post(_PATH, json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    def retrieve(
        self,
        year: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> dict[str, Any]:
        """Read a year: acquired totals, held slices, and the first page of movements.

        ``acquiredMin`` and ``reservedMin`` are published apart and never summed:
        a held slice may still disappear, and one figure would hide that.
        """
        resp = self._client.get(f"{_PATH}/{year}", params=_query(limit, starting_after))
        return resp.json()  # type: ignore[no-any-return]

    def get(self, year: str) -> dict[str, Any]:
        """Alias of :meth:`retrieve`."""
        return self.retrieve(year)

    def list_entries(
        self,
        year: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> dict[str, Any]:
        """Walk the movements page by page, newest first.

        The ledger keeps every movement; a page shows some, and ``next_cursor``
        names the last one returned.
        """
        resp = self._client.get(
            f"{_PATH}/{year}/entries", params=_query(limit, starting_after)
        )
        return resp.json()  # type: ignore[no-any-return]

    def adjust(self, year: str, **params: Any) -> dict[str, Any]:
        """Record turnover made on another channel.

        Args:
            reference: YOUR identifier. It is the entry's identity, so replaying
                the SAME body adds nothing; reusing it for a different one
                answers ``eu_threshold_entry_conflict``. It never becomes a
                document id -- it is hashed, and kept verbatim as data.
            amount: VAT-excluded amount to add, in integer cents. NEVER
                negative: giving an amount back is :meth:`correct`.
            evidence_amount: The art. 24b part of the same movement.
                INDEPENDENT of ``amount``: a domestic electronic service raises
                this counter and not the other.
            external_complete_through_date: Day the other channels are complete
                through after this entry.
            reason: Bounded free text, kept in the audit trail.
        """
        resp = self._client.post(f"{_PATH}/{year}/adjustments", json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    def correct(self, year: str, **params: Any) -> dict[str, Any]:
        """Take a qualified amount back out of the running total.

        This is NOT a negative adjustment. Directive 2006/112/EC art. 90(1)
        reduces the taxable amount of a supply on cancellation, refusal or a
        price reduction after the supply, and the thresholds count the VALUE of
        the supplies -- so the correction NAMES the movement it corrects, its
        qualification, the resource it rests on and its evidence.

        Args:
            reference: YOUR identifier for this correction.
            corrects_entry_id: Movement of THIS ledger whose base is reduced.
                Unknown: ``eu_threshold_correction_target_unknown``.
            kind: ``"credit_note"``, ``"cancellation"`` or ``"refund"``.
            amount: VAT-excluded amount given back, in integer cents. Larger
                than what the corrected movement brought in:
                ``eu_threshold_correction_exceeds_counted``.
            evidence_amount: Its services part.
            related_resource_type, related_resource_id: The resource it rests on.
            evidence_reference: Where the proof lives.
            reason: Why the amount leaves the total.

        Decisions already frozen are never rewritten: they were correct on the
        figures of their own day. Only the total the NEXT operations read changes.
        """
        resp = self._client.post(f"{_PATH}/{year}/corrections", json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    def review(self, year: str, *, reason: str) -> dict[str, Any]:
        """Stop deciding on this ledger: its running total is known to be wrong.

        Every reservation then answers ``eu_threshold_review_required``. This is
        the honest exit when an amount must come out and no qualified correction
        can name the movement it corrects.
        """
        resp = self._client.post(f"{_PATH}/{year}/review", json={"reason": reason})
        return resp.json()  # type: ignore[no-any-return]

    def resolve_review(
        self,
        year: str,
        *,
        reconciled_version: int,
        reconciled_acquired_min: int,
        reconciled_acquired_evidence_min: int,
        evidence_reference: str,
        reason: str,
    ) -> dict[str, Any]:
        """Serve decisions again -- by RECONCILIATION, never by comment.

        A review says the running total is known to be wrong. Reopening the
        ledger on a free-text note would put that same total back in front of the
        next verdict with a sentence for only guarantee. So you state the figures
        you actually verified, and the server compares them to its own:

        Args:
            reconciled_version: Ledger version the reconciliation was carried out
                against. A movement recorded since answers
                ``eu_threshold_reconciliation_stale``.
            reconciled_acquired_min: Acquired total of the common counter, as
                verified. A disagreement answers
                ``eu_threshold_reconciliation_mismatch`` and returns both figures.
            reconciled_acquired_evidence_min: Acquired total of the art. 24b
                counter, as verified.
            evidence_reference: Where the reconciliation itself is filed.
            reason: Why the review is settled.

        What was verified is written into the immutable ``review_resolved``
        movement, with its evidence reference.
        """
        resp = self._client.post(
            f"{_PATH}/{year}/review/resolve",
            json={
                "reconciledVersion": reconciled_version,
                "reconciledAcquiredMin": reconciled_acquired_min,
                "reconciledAcquiredEvidenceMin": reconciled_acquired_evidence_min,
                "evidenceReference": evidence_reference,
                "reason": reason,
            },
        )
        return resp.json()  # type: ignore[no-any-return]


class AsyncEuThresholdLedgers:
    """Asynchronous EU threshold ledger resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def open(self, **params: Any) -> dict[str, Any]:
        """Open a calendar year. See :meth:`EuThresholdLedgers.open`."""
        resp = await self._client.post(_PATH, json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    async def retrieve(
        self,
        year: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> dict[str, Any]:
        """Read the ledger of a year. See :meth:`EuThresholdLedgers.retrieve`."""
        resp = await self._client.get(
            f"{_PATH}/{year}", params=_query(limit, starting_after)
        )
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, year: str) -> dict[str, Any]:
        """Alias of :meth:`retrieve`."""
        return await self.retrieve(year)

    async def list_entries(
        self,
        year: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> dict[str, Any]:
        """Walk the movements. See :meth:`EuThresholdLedgers.list_entries`."""
        resp = await self._client.get(
            f"{_PATH}/{year}/entries", params=_query(limit, starting_after)
        )
        return resp.json()  # type: ignore[no-any-return]

    async def adjust(self, year: str, **params: Any) -> dict[str, Any]:
        """Record turnover made on another channel. See :meth:`EuThresholdLedgers.adjust`."""
        resp = await self._client.post(f"{_PATH}/{year}/adjustments", json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    async def correct(self, year: str, **params: Any) -> dict[str, Any]:
        """Give a qualified amount back. See :meth:`EuThresholdLedgers.correct`."""
        resp = await self._client.post(f"{_PATH}/{year}/corrections", json=_body(params))
        return resp.json()  # type: ignore[no-any-return]

    async def review(self, year: str, *, reason: str) -> dict[str, Any]:
        """Stop deciding on this ledger. See :meth:`EuThresholdLedgers.review`."""
        resp = await self._client.post(f"{_PATH}/{year}/review", json={"reason": reason})
        return resp.json()  # type: ignore[no-any-return]

    async def resolve_review(
        self,
        year: str,
        *,
        reconciled_version: int,
        reconciled_acquired_min: int,
        reconciled_acquired_evidence_min: int,
        evidence_reference: str,
        reason: str,
    ) -> dict[str, Any]:
        """Settle a review. See :meth:`EuThresholdLedgers.resolve_review`."""
        resp = await self._client.post(
            f"{_PATH}/{year}/review/resolve",
            json={
                "reconciledVersion": reconciled_version,
                "reconciledAcquiredMin": reconciled_acquired_min,
                "reconciledAcquiredEvidenceMin": reconciled_acquired_evidence_min,
                "evidenceReference": evidence_reference,
                "reason": reason,
            },
        )
        return resp.json()  # type: ignore[no-any-return]
