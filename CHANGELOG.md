# Changelog

All notable changes to the `facturino` Python SDK are documented here. This
project adheres to [Semantic Versioning](https://semver.org/) and
[Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] - 2026-08-31

The first STABLE tax determination contract. Every invoice is now created from
an immutable tax decision, taken before the document exists, whichever of the
two fiscal journeys takes it.

### Added
- `client.tax_decisions` and `async_client.tax_decisions` with `create()` and
  `retrieve()` (`get()` is an alias): `POST /v1/tax-decisions` and
  `GET /v1/tax-decisions/{id}`. A decision fixes the VAT, the exact
  `amountToCharge` and the three reporting axes for one operation, then never
  changes.
- Two equal fiscal sources, declared with the required `tax_source` argument:
  `"facturino"` (Facturino determines the VAT from the commercial lines and
  the territorial evidence) and `"integration"` (your system supplies the VAT
  of every line: `vat_rate`, `vat_code`, and where the rate is zero a
  `vatex_code` and the line's `place_of_supply`). Supplied VAT is validated
  for coherence — contradictions answer `integration_vat_incoherent`, never a
  silent correction.
- The resource accepts snake_case keyword arguments (`tax_source`,
  `customer_id`, `effective_at`, `price_mode`, `location_evidence`,
  `non_eu_business_evidence`, `retry_of_tax_decision_id`, and per-line
  `rate_category`, `unit_amount`, `related_category`, `place_of_supply_rule`,
  `goods_movement`, `vat_rate`, `vat_code`, `vatex_code`, `place_of_supply`)
  and sends the published camelCase payload. camelCase input is accepted
  unchanged.
- Required `idempotency_key` on `tax_decisions.create()` — non-empty and at
  most 255 characters, checked locally so an over-long key fails immediately
  instead of after a round trip. Sent as the `Idempotency-Key` header so a
  retried request replays the same decision.
- Optional `idempotency_key` on invoice, credit-note and recurring-schedule
  `create()` helpers, including their async counterparts.
- `invoices.create()` forwards `deposits` and `schedule` alongside the
  decision: both are settled server-side against the DECIDED amount due.
- snake_case aliases `tax_decision_id`, `decision_lines` (invoices),
  `credited_lines` (credit notes) and `tax_inputs` (recurring schedules).
- `invoices.bind_tax_decision(invoice_id, tax_decision_id=…, decision_lines=…)`
  and its async twin: `POST /v1/invoices/{id}/bind-tax-decision`. Freezes a
  FINAL decision onto a commercial draft that already exists — the one
  `quotes.convert()` produced — so the quote cycle runs on ONE document:
  convert → decide → bind → finalize. The invoice stays a draft; `finalize()`
  issues it. Idempotent on the decision.

### Changed — BREAKING
- `invoices.create()` requires `taxDecisionId` + `decisionLines` and refuses
  `items`/`lines` locally, before any HTTP call: an invoice never states its
  own VAT. The explicit-tax contract is removed.
- `invoices.update()` no longer accepts commercial or fiscal fields — only
  `dates`, `payment`, `notes`, `purchaseOrderNumber` and `metadata`. To change
  the operation, take a new decision and create a new draft.
- `credit_notes.create()` takes `creditedLines` (fractions of the original
  invoice's frozen lines); `items` is removed. A credit note strictly inherits
  the VAT of the invoice it credits.
- `recurring_invoices.create()` requires `taxInputs` (with its `taxSource`);
  the `templateInvoice.items` template is removed. Each occurrence gets its
  OWN decision on its generation date.
- `TaxSource` values are `"facturino"` and `"integration"` — the two equal
  journeys, and the only two. A commercial draft that has not been decided yet
  reads `taxSource: null`: it states the operation and no fiscal conclusion.
- Default `Facturino-Version` header is `2026-09-01`, the single stable
  contract; the API serves no earlier version.

### Notes
- `tax_decisions.create()` returns the decision on both `201` (created) and
  `200` (the same key already produced it). Reusing a key with a different
  body answers `409`.
- A tax decision is immutable: the resource exposes no update and no delete.
  To re-decide the same operation after supplying missing evidence, create a
  new decision with `retry_of_tax_decision_id`.
- Invoices and credit notes return three status axes — `documentStatus`,
  `transmissionStatus`, `transmissionDetail`, `paymentStatus` — plus
  `taxSource`, `taxDecisionId` / `originalTaxDecisionId` and `taxSnapshot`.
  Responses are plain dicts, so the keys are readable with no code change;
  the `status` key stays populated as their summary projection.

## [1.1.0] - 2026-08-05

### Added
- Document `paypal` as an accepted payment method. The SDK is dynamically typed,
  so the value already passes straight through; the API may add further payment
  method values over time — tolerate unknown values.

## [1.0.1] - 2026-07-25

### Changed
- Packaging/CI: enable `skip-existing` on the PyPI publish workflow; raise the
  minimum supported Python to 3.10 (drop 3.9).

## [1.0.0] - 2026-07-25 — Initial release
