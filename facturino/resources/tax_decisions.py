"""Tax decisions resource — /v1/tax-decisions

A decision is an immutable fiscal position. It fixes the VAT, the exact amount
to charge and the three reporting axes for ONE commercial operation, then never
changes. Ask for a decision BEFORE charging anything: the amount to debit is
``amountToCharge``, not a total computed locally.

Only a ``final`` decision carries amounts. On ``pending_verification`` or
``unsupported``, ``totals`` and ``amountToCharge`` are ``None`` — never ``0``:
absent is not "nothing to charge".

The resource is immutable by design: there is no update and no delete. To
re-decide the same operation after supplying missing evidence, create a new
decision with ``retryOfTaxDecisionId``.

Every decision states its ``taxSource``:

- ``"facturino"`` — Facturino determines the VAT from the commercial lines
  (category, rate category) and the territorial evidence;
- ``"integration"`` — the integration supplies the VAT of every line
  (``vat_rate``, ``vat_code``, and where the rate is zero a ``vatex_code`` and
  the line's ``place_of_supply``). Facturino validates the coherence of what is
  supplied and refuses contradictions with ``integration_vat_incoherent``; it
  never silently corrects a rate.

Both sources produce the same decision object, feed the same reporting
obligations engine and back invoices the same way.

``vat_rate``, ``vat_code`` and ``vatex_code`` describe FRENCH VAT: the contract
has no local-tax jurisdiction, no local tax scheme and no withholding, so the
``"integration"`` source is not a way to pass one through. Where a local tax of a
French overseas collectivity or the TAAF (PM, BL, MF, PF, NC, WF, TF) can change
what is invoiced or what is collected, the decision is not final under EITHER
source. The one sourced exception is a B2B service located in New Caledonia
(art. Lp. 507-1). ``place_of_supply`` is therefore required on every
``"integration"`` line as soon as the buyer is established in one of the seven.

Territoriality, on the other hand, is the SAME under both sources — including the
frontier of the perimeter itself: a seller established outside the French VAT
territory, or a buyer sitting in a territory excluded from the EU VAT territory,
raises under ``"integration"`` exactly the obstacle it raises under
``"facturino"``. A B2C sale to a consumer of another member state — an
electronically supplied service (art. 58) or an intra-EU distance sale of goods
(art. 33(a)) — traverses the same coverage, the same EUR 10,000 threshold, the
same option, the same evidence and the same declarative mechanism whichever
source concluded the VAT. Where ``"facturino"`` produces the rate,
``"integration"`` compares the supplied one to the legal result, at BOTH places
the rule can settle: equal means final, a category no covered B2C supply can
carry or a contradicted ``place_of_supply`` answers
``integration_vat_incoherent``, and a rate neither the destination standard rate
nor the published bands of the seller's own territory confirm leaves the decision
non-final with ``eu_b2c_rate_supplied_mismatch`` — which at origin asserts no
foreign tax, the operation being taxed in France. ``goods_movement`` is therefore
required on a goods line as soon as the buyer is a consumer of another member
state: that movement decides whether the distance-sale rule applies, and it is
never assumed.

A decision reached by that rule carries ``euB2cDestination``: the verdict and its
basis, the threshold figures it was decided on, the declarative mechanism and the
rate entry — registry version, source, verification date, period and region — so
the position can be audited years later without replaying the engine. It is
``None`` on every operation the rule does not reach.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._types import TaxDecision

_PATH = "/v1/tax-decisions"

#: Maximum length the API accepts for ``Idempotency-Key``.
MAX_IDEMPOTENCY_KEY_LENGTH = 255


def _check_idempotency_key(idempotency_key: str) -> str:
    """Validate the key locally, so an over-long one fails without a round trip."""
    key = idempotency_key.strip() if isinstance(idempotency_key, str) else ""
    if not key:
        raise ValueError("Idempotency-Key is required to create a tax decision")
    if len(key) > MAX_IDEMPOTENCY_KEY_LENGTH:
        raise ValueError(
            f"Idempotency-Key must be at most {MAX_IDEMPOTENCY_KEY_LENGTH} characters "
            f"(received {len(key)})"
        )
    return key

#: snake_case aliases accepted on input, so callers stay Pythonic while the HTTP
#: payload always matches the published camelCase contract.
_FIELD_ALIASES = {
    "customer_id": "customerId",
    "customer": "customerId",
    "tax_source": "taxSource",
    "effective_at": "effectiveAt",
    "price_mode": "priceMode",
    "location_evidence": "locationEvidence",
    "non_eu_business_evidence": "nonEuBusinessEvidence",
    "retry_of_tax_decision_id": "retryOfTaxDecisionId",
}

_LINE_ALIASES = {
    "related_category": "relatedCategory",
    "rate_category": "rateCategory",
    "place_of_supply_rule": "placeOfSupplyRule",
    "goods_movement": "goodsMovement",
    "unit_amount": "unitAmount",
    "vat_rate": "vatRate",
    "vat_code": "vatCode",
    "vatex_code": "vatexCode",
    "place_of_supply": "placeOfSupply",
}

_EVIDENCE_ALIASES = {
    "postal_code": "postalCode",
    "third_party": "thirdParty",
    "collected_at": "collectedAt",
    "issued_by_country": "issuedByCountry",
    "issued_by_postal_code": "issuedByPostalCode",
    "reasonable_verification_performed": "reasonableVerificationPerformed",
}


def _rename(mapping: dict[str, str], value: Any) -> Any:
    """Rename snake_case keys of one mapping, leaving everything else alone."""
    if not isinstance(value, dict):
        return value
    return {mapping.get(key, key): item for key, item in value.items()}


def _build_body(params: dict[str, Any]) -> dict[str, Any]:
    """Build the request body in the exact shape the API documents.

    Amounts stay integers and quantities stay strings: a float quantity would
    not survive the round trip, and a quantity is a financial figure.
    """
    body = {_FIELD_ALIASES.get(key, key): value for key, value in params.items()}

    lines = body.get("lines")
    if isinstance(lines, list):
        body["lines"] = [_rename(_LINE_ALIASES, line) for line in lines]

    evidence = body.get("locationEvidence")
    if isinstance(evidence, list):
        body["locationEvidence"] = [_rename(_EVIDENCE_ALIASES, item) for item in evidence]

    body["nonEuBusinessEvidence"] = _rename(
        _EVIDENCE_ALIASES, body["nonEuBusinessEvidence"]
    ) if "nonEuBusinessEvidence" in body else None
    if body["nonEuBusinessEvidence"] is None:
        del body["nonEuBusinessEvidence"]

    return body


class TaxDecisions:
    """Synchronous tax-decisions resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(
        self,
        *,
        idempotency_key: str,
        **params: Any,
    ) -> TaxDecision:
        """Take a decision on a commercial operation.

        Business idempotency is durable here, beyond the 24-hour transport
        window, and it is keyed on the KEY -- not on the operation. The same
        ``idempotency_key`` with the same canonical body always replays the same
        decision, so a retry after a lost response costs nothing and charges
        nothing twice. Two DIFFERENT keys describing the same operation produce
        two decisions: nothing matches them up, and reusing one key with a
        different body answers ``409``.

        Args:
            tax_source: ``"facturino"`` (Facturino determines the VAT) or
                ``"integration"`` (the integration supplies the VAT of every
                line). Required — it decides which shape the lines take.
            customer_id: Customer ID (``cus_...``).
            effective_at: Civil date ``YYYY-MM-DD``. A timestamp is refused: the
                timezone call belongs to the caller.
            currency: ``eur`` only in this ruleset; any other value is refused.
            price_mode: ``tax_exclusive`` or ``tax_inclusive``.
            lines: Commercial lines. ``unit_amount`` in integer cents,
                ``quantity`` as a decimal string. With
                ``tax_source="integration"`` each line also carries its
                supplied VAT: ``vat_rate`` (integer centi-percent),
                ``vat_code`` (S, Z, E, AE, K, G or O) and, when the rate is
                zero, the ``vatex_code`` and ``place_of_supply`` justifying it.
                ``place_of_supply`` is also required as soon as the buyer is
                established in a French overseas collectivity or the TAAF.
            location_evidence: Territorial signals — a country and, where the
                territory needs one, a postal code. Never an IP address, a PSP
                payload or bank account details.
            non_eu_business_evidence: Non-EU business-status proof.
            retry_of_tax_decision_id: Previous decision this one retries. The
                commercial operation must be identical; only evidence may change.
            idempotency_key: Sent as the ``Idempotency-Key`` header. Required,
                255 characters at most. The API answers ``201`` on creation and
                ``200`` when the same key already produced this decision — both
                return the decision. Reusing the key with a different body
                answers ``409``.
        """
        _check_idempotency_key(idempotency_key)
        resp = self._client.post(
            _PATH,
            json=_build_body(params),
            idempotency_key=idempotency_key,
        )
        return resp.json()  # type: ignore[no-any-return]

    def retrieve(self, tax_decision_id: str) -> TaxDecision:
        """Read a decision back — typically after a payment capture, to check
        that the captured amount, currency and buyer match what was decided."""
        resp = self._client.get(f"{_PATH}/{tax_decision_id}")
        return resp.json()  # type: ignore[no-any-return]

    def get(self, tax_decision_id: str) -> TaxDecision:
        """Alias of :meth:`retrieve`, matching the other resources."""
        return self.retrieve(tax_decision_id)


class AsyncTaxDecisions:
    """Asynchronous tax-decisions resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        idempotency_key: str,
        **params: Any,
    ) -> TaxDecision:
        """Take a decision on a commercial operation. See :meth:`TaxDecisions.create`."""
        _check_idempotency_key(idempotency_key)
        resp = await self._client.post(
            _PATH,
            json=_build_body(params),
            idempotency_key=idempotency_key,
        )
        return resp.json()  # type: ignore[no-any-return]

    async def retrieve(self, tax_decision_id: str) -> TaxDecision:
        """Read a decision back. See :meth:`TaxDecisions.retrieve`."""
        resp = await self._client.get(f"{_PATH}/{tax_decision_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, tax_decision_id: str) -> TaxDecision:
        """Alias of :meth:`retrieve`."""
        return await self.retrieve(tax_decision_id)
