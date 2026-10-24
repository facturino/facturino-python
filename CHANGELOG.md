# Changelog

All notable changes to the `facturino` Python SDK are documented here. This
project adheres to [Semantic Versioning](https://semver.org/) and
[Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [2.11.0] - 2026-10-24

### Added
- `TaxDecision["notices"]` and the `TaxDecisionNotice` typed dict (`code`, `detailCode`, `message`, `reference`, `lineId`): what the decision retained and what the seller can do next. Always present, empty when there is nothing to report. Notices never stand for a missing fact: show them to the seller, and act only on a `final` decision.
- `taxSnapshot["notices"]` on invoices and credit notes: the notices frozen with the decision.
- `TaxDecisionIssue` typed dict: `detailCode`, `reference` and `lineId`, already sent by the API.
- `TaxDecision["customer"]["retainedVatNumber"]`: the VAT number the decision retained, the only one the document and its electronic invoice carry; `vatNumber` stays the declared number. Absent on a decision taken before the field existed.
- `customer["natureBasis"]` can read `declared_business_not_evidenced` only within art. 18(2), second subparagraph, of Implementing Regulation (EU) 282/2011: telecommunications, broadcasting and electronically supplied services to a buyer established in the EU VAT territory (Monaco included) who communicated no VAT number. The buyer is treated as a non-taxable person, with a notice. A communicated but unvalidated number leaves `eu_b2b_vat_number_not_validated` pending; INSEE categories 7, 8 and 9 without `taxStatus` keep their refusal.
- `customer["natureBasis"]` can read `declared_non_taxable` for a customer declared `taxStatus: non_taxable`. A legal person carrying a VAT number is checked through VIES: a valid number makes its services follow taxable-person rules (CGI art. 259-0); an unreachable VIES leaves `vies_unavailable` pending. For goods dispatched to another member state or to XI, an unreachable VIES also leaves `vies_unavailable` pending.
- Optional `TaxDecision["legalCategory"]` and the exported `TaxDecisionLegalCategory` type: the SIRENE consultation frozen with the decision (`source`, `siren`, `status`, nullable `legalCategoryCode`, `checkedAt`). Absent when no consultation was due, including historical responses; status and category code stay open strings.
- Optional `place_of_supply_rule` on integration tax decision lines: the seller declares the rule and answers for it; when absent, the general rule (`general`) applies; a derogation the engine does not implement (CGI art. 259 A, 259 B…) leaves the decision `unsupported` (`place_of_supply_rule_not_implemented`); `place_of_supply` accepts 2 to 16 characters.
- Optional `Customer.taxStatus` (`taxable` or `non_taxable`) on creation, update and read.
- Optional `sellerProfile.localTaxRegistrations` on tax decisions, with dated territory registrations (`territory`, `reference`, `effectiveFrom`, nullable `effectiveTo`); exported `TaxDecisionSellerProfile` and `LocalTaxRegistration` types preserve other profile fields.
- Optional `localTaxExemption` on both tax-decision input line types; optional `localTax` on decided lines and invoice items, with the shared exported `LocalTax` typed dict (`code`, `rateCentipercent`, `amount`, `reference`, nullable `exemption`).
- Optional `totalLocalTax` in tax-decision totals and invoice `Totals`, in integer cents. Local-tax codes, territories and exemption reasons stay open strings for future values; historical omissions remain valid.
- `TaxDecisionLine`, `TaxDecisionTotals` and `TaxDecisionSellerProfile` response TypedDicts, plus `TaxDecisionLineInput` in `facturino._types`. Existing plain-dict tax-decision annotations remain compatible; `local_tax_exemption` is accepted as a Python input alias.
- Optional product `kind` (`goods` or `service`) and open-string `supplyCategory` on creation, update and read: both are now stored and returned. Product create/update parameters also expose `tags` and `vatexCode`; `reference`, `category` and `active` remain available on update.
- Optional `kind` and open-string `supplyCategory` on quote input lines; `supplyCategory` is returned on quote lines and copied unchanged when a quote is converted to a draft invoice. Historical omissions stay undeclared.

### Changed
- `vatexCode` on invoice lines, credit-note lines, products and tax-decision lines now takes the official CIUS-FR list (88 codes, for example `VATEX-FR-CGI261-4`, `VATEX-FR-CGI261-7`, `VATEX-FR-CGI295`, `VATEX-EU-132-1I`). The legacy spellings `VATEX-FR-261` and `VATEX-FR-AUTOLIQ` are still accepted and are stored and returned under their official codes (`VATEX-FR-CGI261-4`, `VATEX-FR-AE`); a document issued earlier keeps the code it was issued with. The API contract date remains 2026-09-01.
- `TaxDecisionLine.category` may be `null` only on a `pending_verification` decision for a quote/draft line whose supply category was not declared (`supply_category_not_declared`), without decided amounts. `POST /v1/tax-decisions` still requires `category` on every line under both sources.

### Documentation
- `supply_category_not_declared`: a service line without a declared `supplyCategory` is read under `services` and `electronically_supplied_services`. The same complete result (VAT, category, mentions, local tax and the three obligation axes) gives a `final` decision, `category: services` and a notice; otherwise it gives `pending_verification`, an issue and `category: null`, without amounts. A line with neither `kind` nor `supplyCategory` stays pending without either reading.
- EU threshold ledger: a `reservation_released` movement carries negative amounts when a sale counted for a draft is taken back out before any issuance; it stays at zero for a slice released unconsumed.
- A missing fact leaves `pending_verification`, without amounts, with the fact and remedy in `issues`: `business_status_not_evidenced`, `eu_b2b_vat_number_not_validated`, `non_eu_business_status_not_evidenced`, `vies_unavailable`, `location_evidence_insufficient`, `location_evidence_contradictory`, `location_evidence_relief_undetermined`, `eu_threshold_state_missing` and `goods_movement_unknown`. On `business_status_not_evidenced`, `tax_status_not_declared` names INSEE categories 7, 8 and 9 without `taxStatus`; `legal_category_unresolved` means SIRENE could not give the legal category.
- Unmodelled cases are `unsupported` under `facturino`, and `final` under `integration` with a notice carrying the same code and `foreignTaxReviewRequired: true`; the integrator declares and assumes the tax. This covers `com_taaf_local_regime_not_sourced`, `com_taaf_local_tax_not_determined`, `com_taaf_payment_withholding_not_modelled`, `eu_special_territory_not_implemented` and `non_taxable_legal_person_goods_regime_not_modelled` (goods dispatched to another member state or XI for a non-taxable legal person that communicated a VAT number). A general service to a Saint-Martin consumer without `localTaxExemption` carries `com_taaf_local_regime_not_sourced`, `detailCode: french_vat_and_tgca_cumulation`.
- Overseas cases settled by a collectivity's text stay `final` under both sources: New Caledonia where the taxable buyer accounts for the tax, Saint-Barthélemy, Saint-Pierre-et-Miquelon, and goods shipped to Saint-Martin. An operation located there is outside French VAT (category `O` at 0); a positive French VAT rate under `integration` answers `422 integration_vat_incoherent`. A seller established there stays `unsupported` (`seller_com_taaf_local_tax_not_determined`).
- Saint-Martin TGCA is decided under both sources: a registration in force in `sellerProfile.localTaxRegistrations` gives 4% per line in `localTax`; a declared `localTaxExemption` (`cgism_253`, `not_used_in_saint_martin`) gives 0 with the mention. Without either, the decision is `pending_verification` (`com_taaf_supplier_local_tax_liable`). `totals.totalLocalTax` is included in `totalTTC` and the amount to collect; TGCA is separate from French VAT.
- Both sources refuse a document mixing category `O` with any other category: `unsupported`, `vat_category_o_split_required` (EN 16931 BR-O-11 to BR-O-14); issue two documents. An EU address missing the postal code needed to distinguish VAT territories stays non-final under both sources (`destination_regional_scope_undetermined`); supply the postal code.
- Notices explain a retained result: destination VAT invoiced without a declared mechanism (`destination_mechanism_missing`, with registration guidance), a consumer territory established by two concordant items of different kinds or by the same complete tax result on every possible territory, a VAT number set aside because national registration establishes status, and unmodelled local taxes under `integration`. Complete the facts on a `pending_verification` decision; an `unsupported` decision explains its refusal. Act only on `final`.
- Document the optional customer status, dated local-tax registrations, exemption reasons and separate local-tax amounts and totals. API contract date remains 2026-09-01; package version stays 2.11.0.

### Notes
- New error codes: `tax_decision_retake_required` (409), `einvoicing_buyer_siren_missing` (400), `draft_finalization_in_progress` (409).
- The API contract date remains 2026-09-01: every addition is compatible.

## [2.10.0] - 2026-09-14

### Added
- Add read-only obligation follow-up and autonomous recovery events for invoices, credit notes, collections and e-reporting. Technical recovery is owned by Facturino; manual retry routes remain optional.
- Preserve historical omissions, explicit null and original platform reasons. API date remains 2026-09-01.
- Add the `connect_platform` obligation action: the customer must connect or reconfigure a platform before Facturino resumes; `investigate` is a technical incident handled by Facturino.
- Read-only seller routing: `einvoicing.senderRoutingIdentifier` and `submissionArtefact.sellerRoutingIdentifier`.
- `payment.received` exposes nullable `paymentId` and `fr212`; historical events may omit them. Event amounts remain decimal euro strings, and `total_due` remains the invoice total. API date unchanged.

### Registry disclosure
- Customer lookups expose `disclosure.status` and `disclosure.withheldFields`; protected names and addresses are empty, never invented. Older responses can omit disclosure.

## [2.9.0] - 2026-09-11

### Added
- Registry lookups report the fields the public registry withholds instead of
  returning its non-disclosure placeholder as a name or an address.
- `buyer_identity_not_disclosed`: refused when a customer, an invoice or a
  credit note carries a registry placeholder as the buyer identity, at customer
  write, at finalization and at deposit. A total cancellation credit note may
  carry the corrected identity of the same customer.

## [2.8.0] - 2026-09-10

### Added
- `einvoicing.senderRoutingIdentifier` and
  `einvoicing.submissionArtefact.sellerRoutingIdentifier`: the address the
  platform registered for the seller, used for the deposit, read-only.
- `payment.received` now names the payment that triggered it (`paymentId`) and
  carries its collection state (`fr212`). Movements recorded before this release
  stay `null` rather than guessed.

### Notes
- `total_due` in `payment.received` is the invoice total, not the balance; the
  balance is `amountDue`. That event uses decimal euro strings while the REST
  API uses integer centimes.
- Rate limit headers are now present on every `/v1` response, with the value
  `not_applied` where no limit applies.

## [2.7.0] - 2026-09-10


### Added
- Code-based rejection fields: `rejectionCode`, `rejectionSource`,
  `rejectionNote`, verbatim `rejectionReason`, and eleven rejection categories,
  including `addressing_error` and `other`. Closed attempts retain their
  rejection fields in `previousSubmissions`.
- Active recipient `routingIdentifier`, including the submitted CII artefact,
  and directory follow-up timestamps `buyerReachableAt` / `directoryCheckedAt`.
- Complete payment `fr212` state, including `awaiting_deposit`, `sentAt`,
  `lastErrorCode`, `lastErrorReason` and `updatedAt`.
- Advisory `BuyerNatureWarning` arrays on customers and tax decisions;
  `relatedInvoiceNumber` on credit notes and their events.
- Webhook data exposes coded verdicts and document axes. Structured lifecycle
  entries expose optional `code` and `params`; historical details remain readable.

### Compatibility with 2.5.0 and 2.6.0 in Node / Go
- Backfill response models for the nine earlier rejection categories, the
  payment collection status and document event fields, then extend them above.
- Targeted replay, including an endpoint that already received the event,
  returns `EventRetryResult` (`id`, `object`, `retryScheduled`, optional
  `endpointId`), not a complete event. The existing replay method is preserved.

Response TypedDicts are available from `facturino._types`; ordinary dictionaries
remain the runtime result. Synchronous and asynchronous replay share the receipt.

### Transport and response corrections (2026-09-09)

- Correct `Payment.recorded_by` (api/app/system), nullable responses, and event-family payloads; cover the same contract fixtures across all four SDKs.

- Generate a stable idempotency key once per POST call and preserve it through
  transport retries; never automatically retry an unkeyed POST. Explicit caller
  keys take precedence. A new call receives a new key: persist and pass your own
  key for retries across separate calls or process restarts.
- Respect the full `Retry-After`, including HTTP dates, within a default 60-second
  cumulative retry waiting budget; return the original HTTP error when the delay
  exceeds the remaining budget. Configure `auto_idempotency=False` and `retry_budget` (seconds), for sync and async clients.

## [2.4.0] - 2026-09-06

### Added
- `events.retry(event_id, endpoint_id=...)` replays an event to one endpoint,
  even if already delivered. Every event's `data` now carries the document
  fields `number`, `documentStatus`, `transmissionStatus`, `transmissionDetail`,
  `paymentStatus` and `metadata`.

## [2.3.1] - 2026-09-06

### Changed
- `ereporting.create_declaration` documents the eight declaration types
  (`domestic_b2b` and the four `payment_*` types) and the optional per-line
  fields, including `documentType` (`380` / `381`), `originalInvoiceNumber` and
  `originalInvoiceDate` for a credit note.

## [2.3.0] - 2026-09-04

### Added
- `invoices.finalize(invoice_id, payment=...)` (sync and async) — an optional
  collection applied in the SAME transaction as the numbering, so an invoice
  already paid before issuance is ISSUED settled: the original PDF and Factur-X
  are rendered on a settled document. `payment` is the very object
  `payments.create()` takes (integer centimes, `paid_at` alias accepted), and
  the resulting payment is indistinguishable from one recorded afterwards. All
  or nothing: a collection beyond the amount due is refused
  (`422 payment_exceeds_amount_due`) and the invoice stays a draft. Calling
  `finalize(invoice_id)` without a payment is unchanged.

## [2.2.0] - 2026-09-03

### Added
- `ApiError.issues` — the detailed reasons behind one refusal, as a list of
  `{"code", "param", "message"}` mappings. Present on every error class, and an
  EMPTY list when the API sent none, so reading it never needs a `None` check.

### Documented
- **`issues` is ADDITIVE.** The main `code` is unchanged and stays the value to
  branch on; `param` still points at the first field in cause. A refusal that has
  nothing more to say carries no `issues` key at all — an empty array would make
  "no detail available" indistinguishable from "detail computed, and empty".
- **The published code is the most PRECISE stable one.** Where the main code
  covers several distinct facts, the entry names the actual one: a buyer
  territory that would not resolve answers `validation_error` as the main code
  and `invalid_postal_code` or `territory_conflict` as the detail.
- **`param` is never a guess.** It is filled only where the mapping holds for
  every request — `invalid_postal_code` → `customer.address.postalCode`,
  `territory_conflict` → `customer.address.country`, a reason carried by a line →
  `lines[<index>]` — and is absent otherwise: an approximate pointer would send
  the caller to correct a field that was right.
- The reasons come from the tax decision engine, so they reach the refusals of
  `POST /v1/tax-decisions` and of every endpoint that takes a decision on the
  way — invoices, credit notes, quotes, recurring invoices. Messages carry no
  personal data.

## [2.1.0] - 2026-09-02

### Added
- `eu_threshold_ledgers` resource (sync and async) — the annual ledger the two EU
  B2C thresholds are assessed on: `open()`, `retrieve()` / `get()`,
  `list_entries()`, `adjust()`, `correct()`, `review()` and `resolve_review()` on
  `/v1/eu-threshold-ledgers`. The running totals are a LEDGER — per company, per
  mode and per calendar year — not figures on the fiscal profile.

### Documented
- **Two counters, strictly apart and INDEPENDENT.** The same movements feed the
  common EUR 10,000 threshold (art. 59c(1) — intra-EU distance sales of goods AND
  cross-border services to consumers) and the EUR 100,000 location-evidence
  threshold (Reg. 282/2011 art. 24b — electronically supplied services, domestic
  ones included). A distance sale of goods raises the first and never the second;
  a domestic electronic service raises the second and never the first. Neither
  bounds the other, so every figure comes in a PAIR (`amount` /
  `evidenceAmount`, `acquiredMin` / `acquiredEvidenceMin`…) rather than as a
  total and a share of it.
- **Acquired and reserved are published apart, and never summed.** `acquiredMin`
  is what the year has certainly made; `reservedMin` is the slices held right now
  by operations still being decided. A held slice may still disappear, and one
  combined figure would hide exactly that.
- **An abandoned operation leaves nothing behind.** A verdict is frozen only when
  it holds at BOTH bounds of the running total — with every concurrent slice
  counted, and with none of them — so a released slice simply disappears
  (`reservation_released`, amount zero) instead of being kept as turnover that
  never existed. When the cap falls between the two bounds, nothing is frozen:
  `eu_threshold_concurrent_decision_pending`, and the same operation decides
  cleanly once the concurrent ones conclude.
- **A decision is never frozen without its slice.** If the slice has disappeared
  when the decision is about to be written, the transaction is abandoned — no
  decision, no audit entry, no settled claim (`409
  eu_threshold_reservation_lost`) — and the ledger goes under review on a path of
  its own, which is what makes the review survive that abandonment.
- **Giving an amount back is a QUALIFIED correction, never a negative
  adjustment.** Directive 2006/112/EC art. 90(1) reduces the taxable amount of a
  supply on cancellation, refusal or a price reduction after the supply, so a
  correction names the movement it corrects, its qualification, the resource it
  rests on and its evidence. A movement gives back what it brought in ONCE,
  whatever the number of corrections: the balance is kept inside the same
  transaction, and every entry publishes its `remainingMin`. `correctsEntryId` is
  restricted to the ids the ledger mints — it reaches a document path, and free
  text must not. `eu_threshold_correction_target_unknown`,
  `eu_threshold_correction_target_not_correctable`,
  `eu_threshold_correction_exceeds_counted`.
- **A ledger can stop deciding, and only a reconciliation reopens it.**
  `status: "review_required"` blocks every new reservation
  (`eu_threshold_review_required`) when the running total is known to be wrong.
  Settling it is a RECONCILIATION, never a comment: you state the version you
  checked and the two acquired totals you verified, and only an exact agreement
  reactivates the ledger (`eu_threshold_reconciliation_stale`,
  `eu_threshold_reconciliation_mismatch`). What was verified is written into the
  immutable `review_resolved` movement, with its evidence reference.
- **An ACTIVE Union one-stop-shop registration settles the place.** For a French
  seller, registering for the scheme is how the option of art. 59c(3) is
  exercised: the place is then the destination and the threshold has nothing left
  to decide (`basis: "oss_union_registration"`, `threshold: null`). The
  registration is DATED — one opened in October decides nothing for a September
  sale, one that ended decides nothing any more. Sourced for France only: the way
  the option is exercised is fixed by the member state where it is exercised.
- **The art. 24b single-evidence relaxation is COMPUTED, never declared.** It is
  read off the ledger's EUR 100,000 counter and published on the decision as
  `euB2cDestination.evidenceRelief`, with the totals it rested on.
  `undeterminable` is a first-class answer — two items of evidence are then
  required, and `location_evidence_relief_undetermined` says which fact is
  missing. The seller profile carries no relief flag: a figure is not a checkbox.
- **The seller profile carries DATED registrations.** `euB2cDestination` holds
  the option for taxation at destination, the one-stop-shop registrations
  (`ossRegistrations`) and the local VAT registrations, all with their periods.
  There are no undated `oss` booleans and no IOSS flag: a scheme without a period
  cannot say whether it covered the day of the operation, and no rule of this
  engine reads an import scheme.
- **Completeness dates are checked, never clamped**: a date must belong to the
  ledger's own year (`eu_threshold_date_outside_year`) and must never be in the
  future (`eu_threshold_date_in_future`). `opening.declaredAt` is the ISO instant
  the declaration was made, not the day it declares complete. The calendar year
  itself is bounded by one shared check (`eu_threshold_year_invalid`).
- **Movements are append-only and paginated with a cursor** (`limit`,
  `starting_after`); an adjustment is idempotent on your own reference, compared
  through a canonical fingerprint of the WHOLE body
  (`eu_threshold_entry_conflict`). The reference never becomes a document id: it
  is hashed and kept verbatim as data.
- A profile revision is an immutable RULE that decisions freeze; a turnover total
  moves with every sale and gets corrected — which is why the two are kept apart.
  A revision written earlier may still carry an old `threshold` snapshot, the
  undated `oss` booleans or a `locationEvidenceRelief` flag: all three are
  IGNORED, never read as a counter, a scheme or a figure. Such a revision stays
  valid for every operation the EU B2C rule does not reach; only a covered one
  asks for the facts it lacks.
- Opening a year declares four figures — the previous year's total and the total
  already made this year, each on its own counter — plus the COVERAGE MODE. `facturino_only` is a
  declaration that every covered sale goes through Facturino; `mixed_channels`
  says other channels exist, and the ledger then serves a decision only up to
  the day those channels are declared complete through
  (`eu_threshold_external_coverage_incomplete`). Sales made elsewhere are never
  assumed absent, and no year is ever assumed to start at zero
  (`eu_threshold_state_missing`).
- A decision RESERVES its slice of the running total in a transaction, then
  CONSUMES it in the same transaction that writes the decision: two concurrent
  operations never start from the same figure, a replay of the same
  `Idempotency-Key` counts nothing twice, and a decision that does not conclude
  gives its slice back. An operation dated before one already counted is refused
  (`eu_threshold_backdated_operation`) rather than silently recomputed.
- Adjustments are append-only and idempotent on the caller's own reference. They
  never lower a total: giving an amount back is a QUALIFIED correction naming the
  movement it corrects (Directive 2006/112/EC art. 90(1)), and what cannot be
  qualified that way puts the ledger under review rather than being subtracted.
- `TaxDecision.euB2cDestination.threshold` now freezes the ledger slice itself:
  which ledger, at which version, at which position in its total order, under
  which coverage mode, with the opening figures, the adjustments folded in, the
  total before, the operation's own value and the total after.
- The removed non-final codes (`destination_threshold_declaration_missing`,
  `…_stale`, `…_not_exhaustive`, `…_incomplete`) are replaced by the ledger's
  own: `eu_threshold_state_missing`,
  `eu_threshold_external_coverage_incomplete`, `eu_threshold_backdated_operation`.
- The `integration` source is not a channel for a non-French tax. `vat_rate`,
  `vat_code` and `vatex_code` describe French VAT; the contract carries no
  local-tax jurisdiction, no local tax scheme and no withholding. Where a local
  tax of a French overseas collectivity or the TAAF can change what is invoiced
  or what is collected, the decision is not final under EITHER source
  (`com_taaf_local_tax_not_determined`, `com_taaf_local_regime_not_sourced`,
  `com_taaf_payment_withholding_not_modelled`,
  `seller_com_taaf_local_tax_not_determined`). A B2B service located in New
  Caledonia stays final under both sources: art. Lp. 507-1 makes the taxable
  customer account for the local tax itself.
- `place_of_supply` is required on every `integration` line as soon as the buyer
  is established in one of those seven territories; omitting it answers
  `422 integration_vat_incoherent`. It was previously required only when the
  SELLER was established there.
- The exception for New Caledonia reaches only a supplier NOT established in New
  Caledonia: art. Lp. 507-1 puts the taxe générale sur la consommation on the
  taxable customer of a supplier established outside the territory. A seller
  established there is the ordinary collector of that tax on its own sales, and
  its decision is not final either.
- B2C sales to consumers of other member states are decided by FOUR separate
  questions: is the operation covered by a destination rule, does the common
  EUR 10,000 threshold still allow taxation at origin, did the seller opt for
  destination, and how is the tax declared. The one-stop shop is the fourth
  question only: registering never moves a place of taxation, and not registering
  never restores the seller's own national VAT — it leaves the decision without
  an amount (`destination_mechanism_missing`).
- The threshold figures live in the annual LEDGER, never on the fiscal profile
  (superseded above), because the same threshold counts the sales invoiced
  elsewhere. Non-final codes of the earlier design, all replaced by the ledger's:
  `destination_threshold_declaration_missing`,
  `destination_threshold_declaration_stale`,
  `destination_threshold_declaration_not_exhaustive`,
  `destination_threshold_operation_value_missing`,
  `destination_threshold_price_mode_ambiguous`,
  `destination_threshold_declaration_incomplete`,
  `destination_option_period_invalid`,
  `destination_option_scope_not_sourced`,
  `destination_establishment_in_member_state`,
  `franchise_destination_taxation_not_modelled`.
- A declared figure carries the day through which it is COMPLETE. A total closed
  on 1 March says nothing about the sales of 2 March: it can still prove the
  threshold is passed, never that it is not
  (`destination_threshold_declaration_incomplete`).
- Under a tax-inclusive price the threshold bounds the VAT-exclusive value with
  the only rates the operation can legally bear — the seller's own and the
  destination's — instead of the extremes of the whole Union.
- Destination rates come from a local, dated, versioned registry: no network call
  during a decision, and only the STANDARD rate of the 27 member states is
  tabulated (`destination_rate_band_not_available`,
  `destination_rate_not_sourced_for_date`). A region publishing its own standard
  rate never blocks a whole member state; what governs it decides the answer:
  where the rate follows the PLACE, the region is a territory of its own and the
  address decides (Portugal: mainland 23%, Madeira 22%, Azores 16%; an address
  placing no region answers `destination_regional_scope_undetermined`); where the
  rate is reserved to operations carried out in the zone by a supplier
  ESTABLISHED there, a supplier at distance is taxed at the national rate,
  finally — Austrian Jungholz and Kleinwalsertal (20%, not 19%) and the Greek
  island regime FOR SERVICES, where an electronically supplied service from
  France is taxed at 24%, in Athens and in Kalymnos alike, with no postal
  cartography needed to answer; and where the rate follows the DESTINATION over a
  zone this registry does not cartography, the operation is REFUSED with
  `destination_regional_regime_not_sourced` — this is Greece FOR GOODS, whose
  islands of fewer than 20,000 inhabitants apply a reduced standard rate to the
  goods delivered there since 2026-01-01, intra-community acquisitions included.
  An intra-EU distance sale of goods to Greece is therefore refused, in Athens as
  in Kalymnos, and never taxed at 24% by default. The answer is given per FAMILY
  of operation: the same member state can be settled for services and left open
  for goods.
- The `integration` source traverses the SAME destination rule as `facturino`:
  same coverage, threshold, option, evidence and declarative mechanism, and the
  SAME territorial frontier — a seller outside the French VAT territory or a
  buyer in a territory excluded from the EU VAT territory raises there exactly
  the obstacles it raises here. It compares the supplied rate to the legal result
  instead of producing it, at BOTH places the rule can settle: the destination
  standard rate, or the published bands of the seller's own territory. Equal
  means final; a category no covered B2C supply can carry (`AE`, `K`, `G`, `O`)
  or a contradicted `placeOfSupply` answers `422 integration_vat_incoherent`; a
  rate neither confirms leaves the decision non-final with
  `eu_b2c_rate_supplied_mismatch`. At origin that refusal asserts NO foreign tax:
  the operation is taxed in France. Obstacles keep their meaning —
  `pending_verification` when a fact is missing, `unsupported` when no rule
  covers the case — and `foreignTaxReviewRequired` is asserted only where a tax
  outside French VAT may really be due.

### Documented
- `goods_movement` (`goodsMovement` on the wire) is REQUIRED on a goods line as
  soon as the buyer is a consumer established in another member state, under
  BOTH sources. The alias was already accepted on any line; what changes is that
  the API now refuses the line without it rather than assuming a movement.
- A decision reached by the destination rule carries `euB2cDestination`: verdict
  and basis, the threshold figures it was decided on, the declarative mechanism,
  and the rate entry with its registry version, its source, its verification
  date, its period and its region. `None` on every operation the rule does not
  reach.

No API surface of this SDK changed: decisions are returned as mappings, and
these facts are properties of the REST contract this version already speaks.

### Contract note

- The dated API contract stays `2026-09-01`. The `SellerTaxProfile` schema of that
  first publication carried two fields, `oss` and `locationEvidenceRelief`, which
  are replaced by `euB2cDestination`. `oss` carried a declarative mechanism alone,
  without the place option and the local registrations that decide alongside it;
  `locationEvidenceRelief` was a checkbox where the art. 24b relaxation is a
  FIGURE, computed by the engine on the EUR 100,000 counter of the annual ledger.
  The date is kept because the correction lands before any external consumer: no
  integration ever received the two removed fields, so nothing is broken and there
  is no dated version to keep alongside. A correction of this kind is admissible
  only before a consumer exists; afterwards only a new date would be.

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
- `settledObligations` on a decision: the obligation axes French law settles
  even when the decision is NOT final. The three top-level axes stay `None` on
  such a decision — an axis is never read off a decision that did not conclude —
  while an obligation that stands is carried as a value rather than lost with
  the amount. `None` on a final decision, where the top-level axes are the
  settled ones. It authorises nothing: a non-final decision is not invoiceable
  and opens no payment.
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
