"""Tax decisions resource — /v1/tax-decisions

A decision is an immutable fiscal position. It fixes the VAT, the exact amount
to charge and the three reporting axes for ONE commercial operation, then never
changes. Ask for a decision BEFORE charging anything: the amount to debit is
``amountToCharge``, not a total computed locally.

Only a ``final`` decision carries amounts. On ``pending_verification`` or
``unsupported``, ``totals`` and ``amountToCharge`` are ``None`` — never ``0``:
absent is not "nothing to charge".

A service line of a quote or draft without a declared ``supplyCategory`` is read
under ``services`` and ``electronically_supplied_services``. The same complete
result (VAT, category, mentions, local tax and the three obligation axes) gives a
``final`` decision with ``category: services`` and a
``supply_category_not_declared`` notice. Otherwise the decision is
``pending_verification``, with that issue, ``category: None`` and no amounts.
A line with neither ``kind`` nor ``supplyCategory`` stays pending without either
reading. Direct ``POST /v1/tax-decisions`` still requires ``category`` on every
line under both sources; its input does not inherit this response nullability.

A decision also carries ``notices``: what it retained and what the seller can
do next. Always present, empty when there is nothing to report. Notices never
stand for a missing fact: show them to the seller, and act only on a ``final``
decision. ``issues`` gives the missing fact and remedy on ``pending_verification``
or explains an ``unsupported`` refusal. Facturino never replaces a missing fact
with an assumption. Main pending codes are ``business_status_not_evidenced``,
``eu_b2b_vat_number_not_validated``, ``non_eu_business_status_not_evidenced``,
``vies_unavailable``, ``location_evidence_insufficient``,
``location_evidence_contradictory``, ``location_evidence_relief_undetermined``,
``eu_threshold_state_missing``, ``goods_movement_unknown`` and
``com_taaf_supplier_local_tax_liable``.

The only legal presumption is art. 18(2), second subparagraph, of Implementing
Regulation (EU) 282/2011: telecom, broadcasting and electronic services to a buyer
established in the EU VAT territory (Monaco included) who communicated no VAT
number. The buyer is treated as a non-taxable person with a notice and
``customer.natureBasis: declared_business_not_evidenced``. A communicated but
unvalidated number leaves ``eu_b2b_vat_number_not_validated`` pending. INSEE
categories 7, 8 and 9 without ``taxStatus`` keep their refusal
(``business_status_not_evidenced``, ``detailCode: tax_status_not_declared``).
``legal_category_unresolved`` means SIRENE could not give the category.

``declared_non_taxable`` means a customer declared ``taxStatus: non_taxable``.
A legal person carrying a VAT number is checked through VIES: a valid number
makes its services follow taxable-person rules (CGI art. 259-0); an unreachable
VIES leaves ``vies_unavailable`` pending. ``natureBasis``, codes and ``detailCode``
stay open strings.

Optional ``legalCategory`` freezes the SIRENE consultation: ``source`` (sirene),
``siren``, open-string ``status`` (found, not_found, unavailable), nullable
open-string ``legalCategoryCode`` and civil-date ``checkedAt`` (YYYY-MM-DD).
It is absent when no consultation was due, including historical responses.

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

The seller profile may carry ``localTaxRegistrations``: a list of ``territory``
(currently ``"MF"``), ``reference``, ``effectiveFrom`` (YYYY-MM-DD) and
``effectiveTo`` (YYYY-MM-DD or ``None``). A commercial line may carry the open
string ``localTaxExemption`` (``local_tax_exemption`` on input), currently
``"cgism_253"`` or ``"not_used_in_saint_martin"``. A decided line may carry
``localTax``: ``code`` (currently ``"tgca_mf"``), ``rateCentipercent`` (integer),
``amount`` (integer centimes), ``reference`` and ``exemption`` (string or ``None``).
Decision and invoice totals may carry ``totalLocalTax`` in integer centimes;
invoice items may carry the same ``localTax`` object. These fields are optional:
historical omissions stay absent, and unknown codes, territories and exemptions
must remain readable. Under both sources, a Saint-Martin registration in force
gives 4% per line; a declared exemption gives 0 with the mention. Without either,
``com_taaf_supplier_local_tax_liable`` leaves ``pending_verification``.
``totalLocalTax`` is included in ``totalTTC``, ``amountToCharge`` and the invoice's
``amountDue``. Local tax is separate from French VAT.

``vat_rate``, ``vat_code`` and ``vatex_code`` describe FRENCH VAT. Local tax
belongs in the separate optional fields above, never in those VAT fields;
the ``"integration"`` source is not a way to pass withholding through.

``vatexCode`` on invoice lines, credit-note lines, products and tax-decision
lines takes the official CIUS-FR list (88 codes, including VATEX-FR-CGI261-4,
VATEX-FR-CGI261-7, VATEX-FR-CGI295 and VATEX-EU-132-1I). Legacy inputs
VATEX-FR-261 and VATEX-FR-AUTOLIQ are stored and returned as VATEX-FR-CGI261-4 and
VATEX-FR-AE. A document issued earlier keeps its code. SDK strings stay open;
the API contract date remains 2026-09-01.

French overseas collectivities and the TAAF (PM, BL, MF, PF, NC, WF, TF) are not
part of France for VAT (CGI art. 256-0). An operation located there is outside
French VAT: category ``O`` at 0. Cases settled by a collectivity's text stay
``final`` under both sources: New Caledonia where the taxable buyer accounts for
the tax, Saint-Barthélemy, Saint-Pierre-et-Miquelon, and goods shipped to
Saint-Martin. A seller established there stays ``unsupported`` with
``seller_com_taaf_local_tax_not_determined``.

Unmodelled cases are ``unsupported`` under ``facturino``, and ``final`` under
``integration`` with a notice carrying the same code and
``foreignTaxReviewRequired: true``; the integrator declares and assumes the tax.
This covers ``com_taaf_local_regime_not_sourced``,
``com_taaf_local_tax_not_determined``, ``com_taaf_payment_withholding_not_modelled``,
a buyer in an excluded EU VAT territory such as the Canary Islands, Ceuta or
Melilla (``eu_special_territory_not_implemented``), and goods dispatched to
another member state or XI for a non-taxable legal person that communicated a
VAT number (``non_taxable_legal_person_goods_regime_not_modelled``).
A general service to a Saint-Martin consumer without ``localTaxExemption``
carries ``com_taaf_local_regime_not_sourced``,
``detailCode: french_vat_and_tgca_cumulation``.

Both sources refuse a document mixing category ``O`` with any other category:
``unsupported``, ``vat_category_o_split_required`` (EN 16931 BR-O-11 to BR-O-14);
issue two documents. An EU address missing the postal code needed to distinguish
VAT territories stays non-final under both sources
(``destination_regional_scope_undetermined``); supply the postal code.

Under ``integration``, a positive French VAT rate on a line located in a
collectivity answers ``422 integration_vat_incoherent``. ``place_of_supply`` is
required on every line as soon as the buyer is established in one of the seven.

Notices explain retained results: destination VAT invoiced without a declared
mechanism (``destination_mechanism_missing``, with registration guidance), a
consumer territory established by two concordant items of different kinds or
the same complete tax result on every possible territory, a VAT number set
aside because national registration establishes status, and local-tax cases
under ``integration``. They never supply a missing fact.

A B2C sale to a consumer of another member state — an
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
    "local_tax_exemption": "localTaxExemption",
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
            lines: Commercial lines. ``category`` is required on every line
                under both sources. ``unit_amount`` in integer cents,
                ``quantity`` as a decimal string. With
                ``tax_source="integration"`` each line also carries its
                supplied VAT: ``vat_rate`` (integer centi-percent),
                ``vat_code`` (S, Z, E, AE, K, G or O) and, when the rate is
                zero, the ``vatex_code`` and ``place_of_supply`` justifying it.
                ``place_of_supply`` (2 to 16 characters) is also required as soon
                as the buyer is established in a French overseas collectivity or
                the TAAF. Any line may carry ``place_of_supply_rule``, the
                territoriality rule of the operation (``general`` when absent,
                under both sources); on an integration line it is the rule under
                which ``place_of_supply`` is checked against the place Facturino
                decides.
                ``local_tax_exemption`` / ``localTaxExemption`` is optional:
                an open string, currently ``cgism_253`` or
                ``not_used_in_saint_martin``.
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
