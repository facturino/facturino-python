# Facturino Python SDK

Official Python client library for the [Facturino API](https://facturino.com/docs/api) — developer-first e-invoicing for France.

[![PyPI version](https://img.shields.io/pypi/v/facturino.svg)](https://pypi.org/project/facturino/)
[![Python versions](https://img.shields.io/pypi/pyversions/facturino.svg)](https://pypi.org/project/facturino/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install facturino
```

Requires Python 3.10+.

## Quick Start

The recommended path is decision-first: identity → final tax decision →
create the decision-backed draft immediately → your chosen collection flow.
Facturino imposes no payment service provider and no payment method: an
immediate capture, a bank transfer, a direct debit or payment on agreed terms
all fit the same contract.

```python
import facturino

client = facturino.Client("fac_test_xxx")

# 1. Decide before the final amount is presented, the invoice is issued,
#    or collection starts.
decision = client.tax_decisions.create(
    tax_source="facturino",   # or "integration" to supply your own VAT
    customer_id="cus_8f2k4m9n",
    effective_at="2026-09-15",
    currency="eur",
    price_mode="tax_exclusive",
    lines=[{
        "reference": "abo-pro",
        "description": "Abonnement Pro",
        "category": "electronically_supplied_services",
        "rate_category": "standard",
        "unit_amount": 2900,   # integer cents
        "quantity": "1",       # decimal STRING, never a float
    }],
    idempotency_key=f"order-{order_id}",
)

# 2. Act only on a final decision. "pending_verification" does not mean
#    "nothing to charge": totals and amountToCharge are None, not 0.
if decision["status"] != "final":
    return ask_for_missing_evidence(decision["issues"])

# 3. Create the decision-backed draft immediately: no VAT is restated.
invoice = client.invoices.create(
    customerId=decision["customerId"],
    taxDecisionId=decision["id"],
    decisionLines=[{"taxLineRef": "abo-pro", "unit": "month"}],
    buyer=buyer_snapshot,
    dates={"issued": "2026-09-15", "due": "2026-10-15"},
    payment=payment_terms,
)

# 4. Choose your collection flow — see the two variants below.
```

**Immediate collection** — capture the decided amount, verify, then finalize WITH the collection:

```python
# Capture exactly amountToCharge through your payment provider, payment
# processor, bank transfer or external collection flow. Carry decision["id"]
# in the provider metadata, order reference or custom reference. The
# settlement keeps its OWN financial reference (charge id, transfer
# wording…): the two identifiers are different things and must stay distinct.
settlement = your_collection_process.capture(
    amount=decision["amountToCharge"],   # never a locally computed total
    currency=decision["currency"],
    metadata={"taxDecisionId": decision["id"]},
)

# Re-read the decision by its own id and verify what was actually captured.
source = client.tax_decisions.retrieve(decision["id"])
assert settlement["amount"] == source["amountToCharge"], "amount mismatch"
assert settlement["currency"] == source["currency"], "currency mismatch"

# Finalize AND record the REAL payment in one call: the numbering and the
# collection land in the same transaction, so the issued original (PDF and
# Factur-X) is rendered on a settled invoice. `payment` is the very mapping
# `payments.create()` takes — its real date, method and the settlement's
# financial reference (never the decision id).
client.invoices.finalize(
    invoice["id"],
    payment={
        "amount": settlement["amount"],
        # transfer, card, check, cash, direct_debit, sepa, paypal or other
        "method": settlement["method"],
        "reference": settlement["reference"],
        "paidAt": settlement["paidAt"],
    },
)

# Send to the platform only on the channel the FROZEN decision states.
if source["invoiceChannel"] == "einvoicing":
    client.invoices.send(invoice["id"])
```

**Payment on terms** — finalize and deliver now, collect later:

```python
client.invoices.finalize(invoice["id"])
if decision["invoiceChannel"] == "einvoicing":
    client.invoices.send(invoice["id"])

# …once the transfer arrives, record the REAL collection date.
client.payments.create(
    invoice["id"],
    amount=decision["amountToCharge"],
    method="transfer",
    reference="VIR-2026-000871",
    paidAt="2026-10-12",
)
```

## Tax Decisions

The full walkthrough lives in [Quick Start](#quick-start). A decision is
immutable: it fixes the VAT, the exact `amountToCharge` and the reporting
obligations of one commercial operation, then never changes. Only a `final`
decision carries amounts, and the amount always comes from the decision —
never from a locally computed total.

`create()` requires an `idempotency_key` (255 characters at most; the SDK checks
it before sending). The API answers `201` on creation and `200` when the same
key already produced that decision — both return the decision. Reusing the same
key with a different body answers `409` and raises `ConflictError`; it is never
retried.

The async client mirrors the same surface:

```python
decision = await async_client.tax_decisions.create(
    **operation, idempotency_key=f"order-{order_id}"
)
source = await async_client.tax_decisions.retrieve(decision["id"])
```

### Optional: carrying the decision id through a PSP

These are examples, not requirements. If you collect through a PSP, keep the
decision id on the payment so step 4 can verify what was actually captured.

Stripe — any field that survives the round trip works; `metadata` is the usual one:

```python
intent = stripe.PaymentIntent.create(
    amount=decision["amountToCharge"],
    currency=decision["currency"],
    metadata={"facturino_tax_decision_id": decision["id"]},
)
```

PayPal has no `metadata`; carry the decision id in `custom_id`, and convert the
cents to decimal units for the order amount:

```python
custom_id = decision["id"]
value = f"{decision['amountToCharge'] / 100:.2f}"
```

### What a decision states

| Key | Meaning |
|---|---|
| `status` | `final`, `pending_verification` or `unsupported`. Only `final` carries amounts. |
| `amountToCharge` | Exact amount to debit, integer cents. `None` unless final. |
| `totals` | `totalHT` / `totalVAT` / `totalTTC`, integer cents. `None` unless final. |
| `invoiceChannel` | `einvoicing` or `none` — whether the invoice travels the network. |
| `transactionReporting` | `ereporting`, `none` or `outside_scope`. |
| `paymentReporting` | `fr212`, `ereporting` or `none`. |
| `settledObligations` | The axes French law settles DESPITE a non-final decision. `None` when final — the three axes above are then the settled ones. Each axis inside is `None` when it depends on the treatment that could not be concluded. It authorises nothing. |
| `foreignTaxReviewRequired` | A foreign tax may apply; review it outside Facturino. |
| `vies` | VIES status only (`valid`, `invalid`, `unavailable`, `invalid_format`). |
| `issues` | What is missing, when the decision is not final. |
| `obligationReasons` | Why each axis carries the obligation it does. |
| `expiresAt` / `expired` | Past this instant the decision no longer opens a payment. |

Facturino decides **French VAT and the matching French obligations**. It does
not provide worldwide tax compliance: when a foreign tax may apply, the decision
says so through `foreignTaxReviewRequired`. An operation whose `invoiceChannel`
is `none` is not deposited on a certified platform — its obligation, if any,
goes through e-reporting.

### Missing evidence, then a retry

Supply the evidence and retry the SAME operation. Send the territorial
**signal**, never the raw one: a country and, where the territory needs it, a
postal code — not an IP address, a PSP payload or bank account details.

```python
retried = client.tax_decisions.create(
    **same_operation,
    retry_of_tax_decision_id=pending["id"],
    location_evidence=[{
        "kind": "billing_address",
        "country": "FR",
        "postal_code": "75002",
        "third_party": False,
        "source": "declared",
        "collected_at": "2026-09-15",
    }],
    idempotency_key=f"order-{order_id}-retry-{pending['id']}",
)
```

## Three Status Axes

A document has three states that do not follow from one another. The historical
`status` key stays populated as their projection.

```python
invoice["documentStatus"]      # draft | finalized | cancelled
invoice["transmissionStatus"]  # not_applicable | pending | sending | deposited | transmitted | approved | rejected
invoice["transmissionDetail"]  # available | received | suspended | refused | None
invoice["paymentStatus"]       # unpaid | partially_paid | paid | partially_refunded | refunded
```

Recording a payment never moves the transmission axis, and a refund does not
erase the collection that happened.

## Quotes: convert, decide, bind, finalize

A converted quote yields a COMMERCIAL draft: it states the operation and no VAT
(`taxSource: None`). Bind a final decision to **that same invoice**, then
finalize it — never create a second one.

```python
converted = client.quotes.convert("quo_abc123")
decision = client.tax_decisions.create(idempotency_key=key, **decision_input)

client.invoices.bind_tax_decision(
    converted["invoiceId"],
    tax_decision_id=decision["id"],
    decision_lines=[{"taxLineRef": "l1", "unit": "unit"}],
)
client.invoices.finalize(converted["invoiceId"])
```

Binding freezes the VAT; `finalize()` issues the invoice. The call is idempotent
on the decision: replaying it returns the same invoice.

## Credit Notes on a Decided Invoice

```python
client.credit_notes.create(
    relatedInvoiceId="inv_1",
    creditNoteType="partial",
    reasonCode="quality",
    # Either `quantity` or `amountTTC`, never both. Omit both to credit the
    # line's whole remaining balance. The VAT is inherited from the invoice.
    creditedLines=[{"taxLineRef": "abo-pro", "amountTTC": 1200}],
)
```

## Recurring Schedules on the Decided Journey

Send `taxInputs` instead of `templateInvoice.items`. A recurrence stores no
decision: each occurrence is decided on its own effective date.

```python
client.recurring_invoices.create(
    customerId="cus_1",
    frequency="monthly",
    startDate="2026-09-01",
    nextGenerationDate="2026-09-01",
    taxInputs={
        "priceMode": "tax_exclusive",
        "lines": [{
            "reference": "abo-pro", "description": "Abonnement Pro",
            "category": "electronically_supplied_services",
            "rateCategory": "standard", "unitAmount": 2900,
            "quantity": "1", "unit": "month",
        }],
    },
    templateInvoice={"paymentTermsDays": 30},
)
```

## Supplying your own VAT (`tax_source: "integration"`)

If your system already determines the VAT — an ERP, a marketplace engine, an
in-house rules service — declare it on the decision instead of asking
Facturino to determine it. Each line then carries the VAT you supply:
`vat_rate` (integer centi-percent), `vat_code` (S, Z, E, AE, K, G or O) and,
when the rate is zero, the `vatex_code` and `place_of_supply` justifying it.
Facturino validates the coherence of the whole (a positive rate with an
exemption code, a franchise seller charging VAT, a reverse charge to a
consumer… are refused with `integration_vat_incoherent`) and never silently
corrects a rate. The decision, the invoice and the reporting obligations then
work exactly as with `tax_source: "facturino"` — the two journeys are equals.

```python
decision = client.tax_decisions.create(
    tax_source="integration",
    customer_id="cus_8f2k4m9n",
    effective_at="2026-09-15",
    currency="eur",
    price_mode="tax_exclusive",
    lines=[{
        "reference": "conseil",
        "description": "Prestation de conseil",
        "category": "services",
        "unit_amount": 10000,
        "quantity": "1",
        "vat_rate": 2000,    # 20.00 % — supplied by YOUR system
        "vat_code": "S",
    }],
    idempotency_key=f"order-{order_id}",
)

invoice = client.invoices.create(
    customerId=decision["customerId"],
    taxDecisionId=decision["id"],
    decisionLines=[{"taxLineRef": "conseil", "unit": "unit"}],
    buyer=buyer_snapshot,
    dates={"issued": "2026-09-15", "due": "2026-10-15"},
    payment=payment_terms,
)
```

### What this source is not

`vat_rate`, `vat_code` and `vatex_code` describe **French VAT**. The contract has
no local-tax jurisdiction, no local tax scheme and no withholding, so this source
is not a way to pass one through.

Where a local tax of a French overseas collectivity or the TAAF
(Saint-Pierre-et-Miquelon, Saint-Barthélemy, Saint-Martin, French Polynesia, New
Caledonia, Wallis-and-Futuna, TAAF) can change what you invoice — or what you
actually collect — the decision is **not final under either source**, with the
same issue code and no amount:

| Issue code | When |
|---|---|
| `com_taaf_local_tax_not_determined` | Non-taxable buyer, operation located in the collectivity (electronically supplied service, CGI art. 259 D). |
| `com_taaf_local_regime_not_sourced` | Taxable buyer, but no official act of the collectivity states who bears its tax. |
| `com_taaf_payment_withholding_not_modelled` | French Polynesia: the client withholds part of the payment at source. |
| `seller_com_taaf_local_tax_not_determined` | The seller itself is established in one of the seven. |

The one sourced exception stays final under both sources: a B2B service located
in **New Caledonia** supplied by a seller **not established in New Caledonia**,
where art. Lp. 507-1 makes the taxable customer account for the taxe générale sur
la consommation itself. That article reaches only a supplier established outside
the territory. A seller established in New Caledonia is the ordinary collector of
the taxe générale sur la consommation on its own sales, at a rate this contract
does not carry, so its decision is not final either
(`seller_com_taaf_local_tax_not_determined`).

Because of this, `place_of_supply` is **required** on every line as soon as the
buyer is established in one of the seven — the place of the operation is what
says whether the local tax is at stake, and it is never assumed
(`422 integration_vat_incoherent` otherwise). A place located in France (goods
that never leave the territory, a general B2C service) keeps the decision final
as anywhere else.

## B2C sales to consumers in other member states

An **electronically supplied service** to a consumer established in another
member state (Directive 2006/112/EC art. 58) and an **intra-EU distance sale** of
goods (art. 33(a)) follow one common regime. A **general** B2C service does not:
it stays taxed where the supplier is established (art. 45), and nothing below
concerns it.

Four questions are answered separately, in this order. Collapsing any two of them
produces a wrong rate:

1. is the operation covered by a destination rule;
2. does the common **EUR 10,000** threshold still allow taxation at origin
   (art. 59c(1));
3. did the seller **opt** for taxation at destination (art. 59c(3));
4. how is the tax due at destination **declared** — Union one-stop shop, or a
   local VAT registration in that member state?

The one-stop shop answers the **last** of the four: it is a way of declaring and
paying a tax, not a rule of place. Not registering never restores the seller's
own national VAT — it leaves the decision without an amount.

That does not make the questions watertight in fact. For a **French** seller,
registering for the Union scheme is how the option of art. 59c(3) is exercised:
an **active** registration therefore settles the place at destination on its own,
and the threshold has nothing left to decide (`basis: "oss_union_registration"`,
`threshold: null`). The registration is dated — one opened in October decides
nothing for a September sale, and one that ended decides nothing any more. It is
sourced for France only: the way the option is exercised is fixed by the member
state where it is exercised, so a seller established elsewhere keeps the ordinary
threshold path and states its option explicitly.

The threshold is an **inclusive** cap of `1000000` centimes excluding VAT, open
only to a seller established in a **single** member state; the operation that
carries the running total past it is itself taxed at destination.

That running total lives in an **annual ledger** — `/v1/eu-threshold-ledgers`,
one per company, per mode and per calendar year — and NOT on the fiscal profile.
A profile revision is an immutable rule that decisions freeze; a turnover total
moves with every sale and gets corrected, so the two are kept apart. Facturino
keeps the register of the operations it receives; the sales made on your other
channels must be brought in by an adjustment, or by the opening declaration:

- **opening a year** declares four figures — the previous year's total and the
  total already made this year, each with its *services* part (see the two
  counters below) — plus the coverage mode: `facturino_only` (every covered sale
  goes through Facturino) or `mixed_channels`;
- **an adjustment** adds the turnover of another channel and moves forward the
  day those channels are declared complete through. Under `mixed_channels` a
  decision is served only up to that day.

**Two counters, strictly apart — and independent.** The same movements feed two
thresholds that do not measure the same thing: the common EUR 10,000 threshold
above, and the EUR 100,000 threshold of Reg. 282/2011 art. 24b that governs how
many items of location evidence are required. The second counts only telecom,
broadcasting and electronically supplied services, **domestic ones included**;
the first counts only **cross-border** supplies. A distance sale of goods raises
the first and never the second — and a domestic electronic service raises the
second and never the first.

Neither bounds the other, in either direction: a publisher selling mostly at home
legitimately declares far more on the evidence counter than on the common one.
That is why every figure comes in a pair (`amount` / `evidenceAmount`,
`acquiredMin` / `acquiredEvidenceMin`, …) rather than as a total and a share of
it, and why the single-evidence relaxation is **computed by the engine** on that
second counter rather than declared by the seller.

**Acquired and reserved are published apart, and never summed.** `acquiredMin`
is what the year has certainly made; `reservedMin` is the slices held right now
by operations still being decided. A held slice may still disappear, and one
combined "total" would hide exactly that.

Nothing is assumed: no year starts at zero on its own, and no sale made elsewhere
is presumed absent. A decision reserves its slice of the total in a transaction
and consumes it with the decision itself, so two concurrent operations never read
the same figure as certain and a replay counts nothing twice. A verdict is frozen
only when it holds at **both** bounds — with every concurrent slice counted and
with none of them — which is what makes an abandoned operation simply disappear
instead of staying in the total as turnover that never existed.

**Giving an amount back is a qualified correction, never a negative
adjustment.** Directive 2006/112/EC art. 90(1) reduces the taxable amount of a
supply on cancellation, refusal or a price reduction after the supply, and the
thresholds count the VALUE of the supplies — so a correction names the movement
it corrects, its qualification, the resource it rests on and its evidence.

A movement gives back what it brought in **once**, whatever the number of
corrections: the ledger keeps each movement's balance inside the same
transaction, and every entry publishes its `remainingMin`. `correctsEntryId` is
restricted to the ids the ledger itself mints — it reaches a document path, and
free text must not.

What cannot be qualified that way is not subtracted at all: the ledger goes
**under review** and stops deciding, rather than freeze verdicts on a total
nobody stands behind. A review is settled by **reconciliation**, never by a
comment: you state the version you checked and the two acquired totals you
verified, and only an exact agreement reopens the ledger.

**A decision is never frozen without its slice.** If the slice it held has
disappeared when the decision is about to be written, the transaction is
abandoned — no decision, no audit entry, no settled claim
(`409 eu_threshold_reservation_lost`) — and the ledger goes under review on a
path of its own, so the review survives that abandonment. Freezing a decision the
running total does not carry would leave the sale inside a decision and outside
the year the next operation reads.

Movements are paginated with a cursor (`limit`, `starting_after`): the ledger
keeps them all, a page shows some.

| Issue code | When |
| --- | --- |
| `eu_threshold_state_missing` | No ledger is open for the year of the operation. Open it: nothing is assumed to be zero. |
| `eu_threshold_external_coverage_incomplete` | Other channels exist and are not declared complete through the operation date. Record an adjustment — even a zero one, which simply states that nothing happened. |
| `eu_threshold_backdated_operation` | The operation predates one already counted, and decisions were frozen on that running total. It is refused rather than silently recomputed. |
| `eu_threshold_concurrent_decision_pending` | Other operations of the company are being decided at this very moment, and the cap falls between "all of them confirmed" and "all abandoned". Nothing is frozen on that: decide again once they conclude. |
| `eu_threshold_review_required` | The ledger is under review — its running total is known to be wrong, and no verdict rests on it until the review is settled. |
| `location_evidence_relief_undetermined` | One third-party item of evidence, and the art. 24b relaxation could not be established: open the year's ledger and declare the services figures, or supply a second item. |
| `eu_threshold_reservation_lost` | The slice this decision held is gone. The decision is refused rather than frozen without it, and the ledger goes under review. |
| `destination_threshold_operation_value_missing` | A line value cannot be sized, so no slice of the total can be taken for it. |
| `destination_threshold_price_mode_ambiguous` | Tax-inclusive price: the VAT-exclusive value depends on the rate the threshold has to decide, and the bounds fall on both sides of the cap. |
| `destination_option_period_invalid` | The option is declared over less than its minimum binding period. |
| `destination_option_scope_not_sourced` | Seller established outside France: the binding period is fixed by the member state where the option is exercised, and only the French one is sourced here. |
| `destination_establishment_in_member_state` | The seller declares an establishment in the destination member state: which establishment supplies then decides both the place and the mechanism, and no fact of the contract names it. A local VAT registration alone is not an establishment. |
| `destination_regional_scope_undetermined` | The member state publishes regional standard rates and the address places none of them — state the customer's postal code. |
| `destination_mechanism_missing` | Destination taxation is due with neither the Union scheme nor a local registration valid for that state on that date. |
| `franchise_destination_taxation_not_modelled` | Seller under the French small-enterprise exemption whose operation is taxed by another member state. |

Rates come from a **local, dated, versioned registry**: no network call during a
decision, and a decision replayed years later reproduces the same rate. A rate
change is a new period, never a rewrite. Only the **standard** rate of the 27
member states is tabulated — the scope of the reduced rates follows a national
classification this contract does not hold, and an ordinary electronically
supplied service is never granted the rate an electronic publication may benefit
from (`destination_rate_band_not_available`). An effect date before the registry
answers `destination_rate_not_sourced_for_date`.

A **region publishing its own standard rate** never blocks a whole member state.
What governs the region decides the answer:

- **the rate follows the place of the operation.** The region is then a territory
  of its own and the address decides: Portugal mainland 23%, Madeira 22%, Azores
  16% (CIVA art. 18, CTT postal ranges). Only an address placing no region at all
  is refused — `destination_regional_scope_undetermined`, naming the missing fact
  rather than falling back on the mainland rate;
- **the rate is reserved to operations carried out in the zone by a supplier
  established there.** A supplier at distance does not acquire it from the
  consumer's address, so the national rate is the final answer — and no postal
  cartography of the zone is needed to say so: Austrian Jungholz and
  Kleinwalsertal (§ 10(4) UStG — 20%, not 19%), and the Greek island regime FOR
  SERVICES, which AADE reserves to a supplier established on the island for an
  operation performed there. An electronically supplied service from France is
  therefore taxed at 24% in Greece, in Athens and in Kalymnos alike;
- **the rate follows the destination and the zone is not cartographied here.**
  Neither the regional rate nor the national one can be asserted, so the
  operation is refused: `destination_regional_regime_not_sourced`, non-final and
  without an amount. This is Greece FOR GOODS: since 2026-01-01 the islands of
  fewer than 20,000 inhabitants apply a reduced standard rate to the goods
  delivered there, intra-community acquisitions included, and the list of those
  islands is not cartographied by postal code here. An intra-EU distance sale of
  goods to Greece is therefore refused — in Athens as in Kalymnos — and never
  taxed at 24% by default. The answer is given per FAMILY of operation: the same
  member state can be settled for services and left open for goods.

### The annual ledger

```python
# Open the year — nothing starts at zero on its own.
client.eu_threshold_ledgers.open(
    year="2026",
    previous_year_amount=250000,      # cents, VAT excluded
    current_year_opening=100000,
    coverage_mode="mixed_channels",   # other channels exist
    external_complete_through_date="2026-01-01",
)

# Bring in what was sold elsewhere. Append-only, idempotent on `reference`.
client.eu_threshold_ledgers.adjust(
    "2026",
    reference="marketplace-2026-08",
    amount=40000,
    external_complete_through_date="2026-09-15",
    reason="Marketplace sales, August",
)

ledger = client.eu_threshold_ledgers.retrieve("2026")
ledger["cumulativeMin"]  # total already acquired, in cents
ledger["remainingMin"]   # what is left before the cap
```

### The same rule under `taxSource: 'integration'`

An integration that concludes its own VAT does not get a different territoriality.
The `integration` source traverses the same coverage, the same threshold, the same
option, the same evidence and the same declarative mechanism; what differs is the
outcome. Where `facturino` **produces** the rate, `integration` **compares** the
one you supply to the legal result:

- equal — decision `final`;
- a category no B2C supply taxed at destination can carry (`AE`, `K`, `G`, `O`),
  or a `placeOfSupply` the rule contradicts — `422 integration_vat_incoherent`;
- a rate neither the destination **standard** rate nor the published bands of the
  seller's own territory confirm — non-final, with
  `eu_b2c_rate_supplied_mismatch`. Facturino holds only the standard rate of
  another member state, and only the bands it publishes for a French territory,
  so it can neither confirm a reduced rate nor correct yours. At origin that
  refusal asserts NO foreign tax: the operation is taxed in France;
- a rule that could not conclude — blocked exactly as under `facturino`, with
  the same meaning of `pending_verification` and `unsupported`.

The confrontation reaches BOTH places the rule can settle, and the territorial
frontier is shared too: a seller established outside the French VAT territory, or
a buyer sitting in a territory excluded from the EU VAT territory, raises under
`integration` exactly the obstacle it raises under `facturino`.

Because of this, `goods_movement` (`goodsMovement` on the wire) is **required** on a goods line as soon as the
buyer is a consumer of another member state: that movement decides whether the
distance-sale rule applies, and it is never assumed.

### What the decision freezes

The decision carries `euB2cDestination`: what the rule concluded, as data rather
than as a sentence — the verdict and its basis, the threshold figures it was
decided on, the declarative mechanism, and the rate entry with its registry
version, its source, its verification date, its period and its region. It is
present as soon as the rule covers a line — including on a decision that is NOT
final, where it states exactly what is missing — and `None` on every operation
the rule does not reach.


## Amount Conventions

All monetary amounts are expressed as **integers in centimes** (1 EUR = 100):

| Value | Integer | Meaning |
|-------|---------|---------|
| 100.00 EUR | `10000` | unitPrice |
| 20.00% | `2000` | vatRate (centipercent) |
| 5.50% | `550` | vatRate (centipercent) |

## Auto-Pagination

List endpoints return a `SyncPage` that automatically fetches subsequent pages when iterated:

```python
# Iterate through ALL invoices, 25 at a time
for invoice in client.invoices.list(limit=25):
    print(invoice["id"], invoice["status"])

# Access a single page without auto-pagination
page = client.invoices.list(limit=10)
print(page.data)       # list of items on this page
print(page.has_more)   # whether more items exist
```

## Filtering and Expanding

List and retrieve calls forward keyword arguments straight through as query
parameters, so any filter the API supports is available without an SDK change:

```python
# Invoices converted from a given quote
for inv in client.invoices.list(convertedFrom="quo_abc123"):
    print(inv["id"])

# Inline a retrieved invoice's credit notes and net balance
invoice = client.invoices.get("inv_abc123", expand="credit_notes")
print(invoice["expanded"]["net_balance"])
for cn in invoice["expanded"]["credit_notes"]:
    print(cn["id"])
# expand accepts a comma-separated list: "customer,items.product,credit_notes"

# Product catalogue filters
results = client.products.list(q="cons", category="services", active=True)
```

Customer contacts accept a `role` (`billing`, `technical` or `main`); the
`billing` contact receives invoices by default:

```python
client.customers.create(
    name="ACME Corp",
    type="company",
    contacts=[
        {"name": "Finance", "email": "ap@acme.com", "role": "billing"},
        {"name": "Ops", "email": "ops@acme.com", "role": "technical"},
    ],
)
```

Credit note numbering is controlled per company via
`creditNoteSettings.numberingMode` — `separate` (default) gives credit notes
their own series, `unified` shares the invoice series:

```python
client.companies.update(
    "comp_abc123",
    creditNoteSettings={"numberingMode": "unified"},
)
```

## Async Support

An async client is available for use with `asyncio`:

```python
import asyncio
import facturino

async def main():
    async with facturino.AsyncClient("fac_test_xxx") as client:
        decision = await client.tax_decisions.create(
            tax_source="facturino",
            customer_id="cus_xxx",
            effective_at="2026-07-01",
            currency="eur",
            price_mode="tax_exclusive",
            lines=[{"reference": "widget", "description": "Widget", "category": "goods",
                    "rate_category": "standard", "unit_amount": 5000, "quantity": "2"}],
            idempotency_key="order-async-1",
        )
        invoice = await client.invoices.create(
            customer="cus_xxx",
            taxDecisionId=decision["id"],
            decisionLines=[{"taxLineRef": "widget", "unit": "unit"}],
            buyer={"companyName": "Acme SAS", "siret": "55208131766522",
                   "address": {"line1": "10 rue de la Paix", "postalCode": "75002", "city": "Paris", "country": "FR"}},
            dates={"issued": "2026-07-01", "due": "2026-07-31"},
            payment={"terms": "30 jours", "termsDays": 30, "method": "transfer", "latePaymentRate": "10.00", "collectionFee": "40.00"},
        )

        async for inv in await client.invoices.list():
            print(inv["id"])

asyncio.run(main())
```

## Available Resources

| Resource | Methods |
|----------|---------|
| `client.tax_decisions` | `create`, `retrieve` (`get` alias) — immutable: no update, no delete |
| `client.invoices` | `create`, `bind_tax_decision`, `list`, `get`, `update`, `delete`, `finalize`, `send`, `cancel`, `remind`, `clone`, `get_pdf`, `get_facturx`, `get_xml`, `get_status`, `verify`, `list_events`, `get_audit_trail`, `generate_audit_trail_pdf`, `create_payment_link`, `create_payment_token` |
| `client.payments` | `create(invoice_id, ...)`, `list(invoice_id)` |
| `client.customers` | `create`, `list`, `get`, `update`, `delete`, `lookup`, `import_csv`, `export_csv` |
| `client.products` | `create`, `list`, `get`, `update`, `delete`, `import_csv`, `export_csv` |
| `client.quotes` | `create`, `list`, `get`, `update`, `delete`, `send`, `accept`, `refuse`, `convert`, `clone`, `get_pdf` |
| `client.credit_notes` | `create`, `list`, `get`, `update`, `delete`, `finalize`, `send`, `email`, `get_pdf`, `get_facturx`, `get_xml` |
| `client.events` | `list`, `get`, `retry` |
| `client.webhook_endpoints` | `create`, `list`, `get`, `update`, `delete` |
| `client.recurring_invoices` | `create`, `list`, `get`, `update`, `delete`, `pause`, `resume` |
| `client.companies` | `list`, `create`, `get`, `update`, `add_milestone`, `upload_cgv`, `get_cgv`, `delete_cgv` |
| `client.exports` | `generate_fec`, `get_fec_status`, `export_invoices`, `get_status` |
| `client.ereporting` | `list`, `get`, `create_declaration`, `submit_declaration` |
| `client.jobs` | `get` |
| `client.sandbox` | `reset_data`, `simulate_status`, `create_fixtures` |
| `client.reference` | `list_legal_forms`, `list_naf_codes`, `list_pa_providers` |
| `client.health` | `check` |

> **Public token endpoints** — the recipient-facing portals (`/pay/:token`,
> `/portal/:token`, `/quote-portal/:token`) are intentionally not exposed by the
> SDK: they are opened by the end recipient through a hosted page, not called
> with an API key.

## Recording Payments

Payments are a sub-resource of invoices:

```python
# Record a payment (amount in centimes)
payment = client.payments.create(
    "inv_xxx",
    amount=12000,          # 120.00 EUR
    method="transfer",
    paid_at="2026-03-15",
    reference="VIR-2026-001",
)

# List payments for an invoice
for payment in client.payments.list("inv_xxx"):
    print(payment["amount"], payment["method"])
```

## Webhook Verification

Verify incoming webhook signatures using HMAC-SHA256:

```python
import facturino

# In your webhook handler (Flask, FastAPI, Django, etc.)
payload = request.body                                    # raw bytes
signature = request.headers["Facturino-Signature"]        # signature header
endpoint_secret = "whsec_..."                             # your endpoint secret

try:
    event = facturino.Webhook.construct_event(payload, signature, endpoint_secret)
    print(f"Received event: {event['type']}")

    if event["type"] == "invoice.paid":
        invoice_id = event["data"]["id"]
        # Handle paid invoice...

except facturino.SignatureVerificationError as e:
    print(f"Invalid signature: {e}")
    # Return 400
```

## Error Handling

All API errors are raised as typed exceptions:

```python
import facturino

client = facturino.Client("fac_test_xxx")

try:
    client.invoices.get("inv_nonexistent")
except facturino.NotFoundError as e:
    print(f"Not found: {e.message}")
    print(f"Request ID: {e.request_id}")
except facturino.AuthenticationError:
    print("Invalid API key")
except facturino.RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except facturino.PlanLimitError:
    print("Feature not available on your plan")
except facturino.ApiError as e:
    print(f"API error {e.status_code}: {e.message}")
```

**Error hierarchy:**

```
FacturinoError
  ApiError
    AuthenticationError     (401)
    PermissionDeniedError        (403)
    NotFoundError           (404)
    InvalidRequestError     (400)
    ValidationError         (422)
    PlanLimitError          (402)
    ConflictError           (409)
    RateLimitError          (429)
    ServerError             (5xx)
  SignatureVerificationError
```

## Retries

The client automatically retries on transient failures (HTTP 429, 500, 502, 503) with exponential backoff. The `Retry-After` header is respected on 429 responses.

```python
# Customize retry behavior
client = facturino.Client(
    "fac_test_xxx",
    max_retries=5,     # default: 3
    timeout=60.0,      # default: 30s
)
```

## Idempotency

An `Idempotency-Key` protects the **replay of one request**. It is not a
deduplicator: the API never decides on its own that two requests "mean the same
thing".

- **Same key + same canonical body** — the first 2xx response is replayed
  verbatim, and the operation is not executed a second time.
- **Same key + different body** — `409 idempotency_error`. A key belongs to a
  request, not to an endpoint.
- **Different keys** — two distinct operations, even with byte-identical bodies.
  Two requests describing the same operation are **not** deduplicated
  automatically; the key, and only the key, declares that two sends are the same
  attempt.
- **Canonical body** — JSON object keys are compared in a stable order, so
  reordering them does not change the request. Changing a value, adding or
  removing a field does. Array order is significant: two lines swapped are two
  different documents.
- **Failure before execution** (validation, read-only field, sanitisation)
  releases the key, so a corrected retry with the same key runs.
- **Business refusal during execution** is stored and replayed; the operation is
  not re-executed.
- **Scope** — 24 hours, per API key. `POST /v1/tax-decisions` additionally
  carries a durable business idempotency that never expires.

All POST requests carry an `Idempotency-Key`. The client generates a UUID v4
when you do not supply one — which makes each call a distinct request. Pass your
own key whenever a retry must replay instead of re-run.

```python
# Same key + same body -> the first response, replayed.
invoice = client.invoices.create(
    customer="cus_xxx",
    taxDecisionId=decision["id"],
    decisionLines=[...],
    idempotency_key="order-4821",
)

# Retry with new evidence is NOT idempotency. It takes a NEW decision on the
# same commercial operation: use a NEW key and link the previous decision.
decision = client.tax_decisions.create(
    **operation,
    retry_of_tax_decision_id=suspended["id"],
    idempotency_key="order-4821-retry-1",
)
```

## Sandbox

Test your integration using sandbox utilities (requires `fac_test_*` API key):

```python
# Reset test data and reload fixtures
result = client.sandbox.reset_data()
print(f"Deleted {result['deleted_count']} items, created {result['fixtures_created']} fixtures")

# Simulate a PA status change
client.sandbox.simulate_status("inv_test_123", "approved")
```

## Development

```bash
git clone https://github.com/facturino/facturino-python.git
cd facturino-python
pip install -e ".[dev]"
pytest -v
ruff check .
mypy facturino/
```

## License

MIT
