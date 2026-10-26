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
    # Complete the facts if pending; explain the refusal if unsupported.
    return handle_non_final_decision(decision["status"], decision["issues"])
#    Notices say what was retained and what the seller can do next.
show_to_seller(decision["notices"])

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

Every line sent to `POST /v1/tax-decisions` requires `category`, under both
sources. Response `TaxDecisionLine.category` can be `None` only on a pending
decision for a quote/draft line whose supply category was undeclared; see the
[quote rules](#quotes-convert-decide-bind-finalize) below.

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

### Optional local-tax fields

Customers accept an optional `taxStatus` (`"taxable"` or `"non_taxable"`) on
creation and update, and return it when present. The seller profile frozen with
a decision may carry `localTaxRegistrations`: a list of `territory` (currently
`"MF"`), `reference`, `effectiveFrom` (`YYYY-MM-DD`) and `effectiveTo`
(`YYYY-MM-DD` or `None`).

A commercial line in `tax_decisions.create()` may carry `localTaxExemption`
(or its Python alias `local_tax_exemption`). This is an open string; documented
values are currently `"cgism_253"` and `"not_used_in_saint_martin"`.

Decision lines and invoice `items` may return `localTax`, separately from VAT:

```python
{
    "code": "tgca_mf",
    "rateCentipercent": 400,  # 4.00%
    "amount": 400,           # integer centimes
    "reference": "CGISM",
    "exemption": None,
}
```

Decision and invoice totals may also return `totalLocalTax` in integer centimes.
It is included in `totalTTC`, the decision's `amountToCharge` and the invoice's
`amountDue`. Under both sources, Saint-Martin TGCA is 4% per line with a
registration in force, or 0 with a declared exemption and its mention. Without
either, the decision stays `pending_verification`
(`com_taaf_supplier_local_tax_liable`). TGCA is separate from French VAT.

All these fields are optional; historical omissions remain absent. `code`,
`territory` and exemption strings accept future values. Response shapes are
documented by `LocalTax`, `LocalTaxRegistration`, `TaxDecisionSellerProfile`,
`TaxDecisionLine` and `TaxDecisionTotals`; existing generic dictionary annotations
on `TaxDecision` are preserved. `TaxDecisionLineInput` is available from
`facturino._types` for the camelCase request shape. No amount is computed locally.

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
| `totals` | `totalHT` / `totalVAT` / `totalTTC`, integer cents; optional `totalLocalTax` is included in `totalTTC` and `amountToCharge`. `None` unless final. |
| `invoiceChannel` | `einvoicing` or `none` — whether the invoice travels the network. |
| `transactionReporting` | `ereporting`, `none` or `outside_scope`. |
| `paymentReporting` | `fr212`, `ereporting` or `none`. |
| `obligationBasis` | Read-only transmission basis frozen with the decision: `legal`, `voluntary_early_adoption` or `None` when no obligation applies or the basis is unresolved. May be absent on historical responses. |
| `settledObligations` | The axes French law settles DESPITE a non-final decision. `None` when final — the three axes above are then the settled ones. Each axis inside is `None` when it depends on the treatment that could not be concluded. It authorises nothing. |
| `foreignTaxReviewRequired` | A foreign tax may apply; review it outside Facturino. |
| `vies` | VIES status only (`valid`, `invalid`, `unavailable`, `invalid_format`). |
| `issues` | What to complete on `pending_verification`, or why `unsupported` is refused. Each entry has a stable `code` and optional `detailCode`, `reference` and `lineId`. |
| `notices` | What the decision retained and what the seller can do next. Always present, empty when there is nothing to report. Notices never stand for a missing fact; show them to the seller. |
| `customer["retainedVatNumber"]` | The VAT number the decision retained — the only one the document and its electronic invoice carry. `None` when none is retained. `customer["vatNumber"]` stays the number as declared. |
| `legalCategory` | Optional SIRENE consultation frozen with the decision: `source` (`sirene`), `siren`, open-string `status` (`found`, `not_found`, `unavailable`), nullable open-string `legalCategoryCode`, and `checkedAt` (`YYYY-MM-DD`). Absent when no consultation was due, including historical responses. Typed as `TaxDecisionLegalCategory`. |
| `obligationReasons` | Why each axis carries the obligation it does. |
| `expiresAt` / `expired` | Past this instant the decision no longer opens a payment. |

Facturino decides **French VAT and the matching French obligations**. It does
not provide worldwide tax compliance: when a foreign tax may apply, the decision
says so through `foreignTaxReviewRequired`. An operation whose `invoiceChannel`
is `none` is not deposited on a certified platform — its obligation, if any,
goes through e-reporting.

### Notices: what a decision retained

Always act only on a `final` decision, and read its `notices` too. Notices say
what the decision retained and what the seller can do next. Examples include
destination VAT invoiced without a declared mechanism
(`destination_mechanism_missing`, with registration guidance), a consumer
territory retained by two concordant items of different kinds or because every
possible territory gives the same complete tax result, a VAT number set aside
because national registration establishes status, and local-tax notices under
`integration`. A notice never stands for a missing fact.

The only legal presumption is art. 18(2), second subparagraph, of Implementing
Regulation (EU) 282/2011: telecommunications, broadcasting and electronically
supplied services to a buyer established in the EU VAT territory (Monaco
included) who communicated no VAT number. The buyer is treated as a non-taxable
person, with a notice and `customer["natureBasis"]` set to
`declared_business_not_evidenced`. A communicated but unvalidated number leaves
`eu_b2b_vat_number_not_validated` pending. INSEE legal categories 7, 8 and 9
without `taxStatus` keep their refusal.

`declared_non_taxable` means the customer declared `taxStatus: non_taxable`.
If that customer is a legal person carrying a VAT number, VIES is consulted:
a valid number makes its services follow taxable-person rules (CGI art. 259-0);
an unreachable VIES leaves `vies_unavailable` pending. `natureBasis`, codes and
`detailCode` stay open strings.

```python
if decision["status"] == "final":
    for notice in decision["notices"]:
        # "code" is stable; "detailCode", "reference" and "lineId" are optional.
        print(notice["code"], notice.get("detailCode"), notice["message"], notice.get("lineId"))
```

The list of codes can grow: treat an unknown code as a generic notice. Invoices
and credit notes freeze the notices of their decision in
`invoice["taxSnapshot"]["notices"]`; a credit note repeats those of the invoice
it credits. The `TaxDecisionNotice` and `TaxDecisionIssue` typed dicts describe
the entries.

The read-only `taxSnapshot["obligationBasis"]` on invoices and credit notes
also freezes the decision's transmission basis: `"legal"`,
`"voluntary_early_adoption"` or `None` when no obligation applies or the basis
is unresolved. Historical snapshots may omit the field. The exported
`TaxSnapshot` type describes the snapshot; existing document annotations keep
accepting plain dictionaries.

### Missing evidence, then a retry

Facturino never replaces a missing fact with an assumption. A missing fact
leaves `pending_verification`, without amounts, with the fact and remedy in
`issues`. Main codes are `business_status_not_evidenced`,
`eu_b2b_vat_number_not_validated`, `non_eu_business_status_not_evidenced`,
`vies_unavailable`, `location_evidence_insufficient`,
`location_evidence_contradictory`, `location_evidence_relief_undetermined`,
`eu_threshold_state_missing`, `goods_movement_unknown` and
`com_taaf_supplier_local_tax_liable`.

On `business_status_not_evidenced`, `detailCode: tax_status_not_declared` names
INSEE categories 7, 8 and 9 (association, public body, foundation) without
`taxStatus`; `legal_category_unresolved` means SIRENE could not give the category;
`einvoicing_buyer_registration_required` names the SIRET the electronic invoice
requires. Supply the missing facts and retry the SAME operation.
An `unsupported` decision explains its refusal. Both sources refuse an EU
address missing the postal code needed to distinguish VAT territories
(`destination_regional_scope_undetermined`); supply the postal code.
Send the territorial **signal**, never the raw one: a
country and, where the territory needs it, a postal code — not an IP address, a
PSP payload or bank account details.

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

## Products

Products accept and return optional `kind` (`"goods"` or `"service"`) and
`supplyCategory`, an open string currently documenting `goods`, `services`,
`electronically_supplied_services`, `deposit` and `ancillary_costs`. Both are now
stored and returned. `kind` describes the document's goods/services classification;
`supplyCategory` declares the fiscal category. An omission stays undeclared.

```python
product = client.products.create(
    name="Monthly subscription",
    unit_price=10000,
    vat_rate=2000,
    vatCode="S",
    unit="month",
    kind="service",
    supplyCategory="electronically_supplied_services",
    tags=["subscription"],
)
client.products.update(
    product["id"], reference="SUB-1", category="subscriptions", active=False,
)
```

Create and update also accept `tags` and the open-string official CIUS-FR
`vatexCode`; update accepts `reference`, catalog `category` and `active`.
`Product`, exported from `facturino`, documents the response shape. Existing
dictionary return annotations are preserved, as are historical field omissions.

## Quotes: convert, decide, bind, finalize

Quote input and returned lines accept optional `kind` and open-string
`supplyCategory`. Conversion copies a declared `supplyCategory` unchanged to the
draft invoice. Missing values stay undeclared; only `kind: goods` gives `goods`.

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

A service line of a quote or draft without a declared `supplyCategory` is read
under `services` and `electronically_supplied_services`. The same complete result
(VAT, category, mentions, local tax and the three obligation axes) gives a `final`
decision with `category: services` and a `supply_category_not_declared` notice.
Otherwise it gives `pending_verification`, an issue with that code and
`category: None`, without amounts. A line with neither `kind` nor `supplyCategory`
stays pending without either reading. Declare the fiscal category to resolve it.
Historical responses are unchanged. Direct `POST /v1/tax-decisions` still
requires `category` on every line under both sources.

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
corrects a rate. Both sources feed the same decision, invoice and reporting
cycle. For an unmodelled case, `facturino` refuses it as `unsupported`;
`integration` stays open with a `final` decision, a notice carrying the same code
and `foreignTaxReviewRequired: True`. The integrator declares and assumes the tax.

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

`vat_rate`, `vat_code` and `vatex_code` describe **French VAT**. Local tax uses
the [separate optional fields](#optional-local-tax-fields), never those VAT
fields. The `integration` source does not accept withholding through them.

`vatexCode` on invoice lines, credit-note lines, products and tax-decision lines
takes the official CIUS-FR list (88 codes, including `VATEX-FR-CGI261-4`,
`VATEX-FR-CGI261-7`, `VATEX-FR-CGI295`, `VATEX-FR-AE`, `VATEX-EU-132-1I`,
`VATEX-EU-I` and `VATEX-EU-J`). Legacy inputs `VATEX-FR-261` and
`VATEX-FR-AUTOLIQ` are stored and returned as `VATEX-FR-CGI261-4` and
`VATEX-FR-AE`; a document issued earlier keeps the code it was issued with.
SDK fields remain open strings; the API contract date remains 2026-09-01.

Both sources refuse a document mixing category `O` with any other category:
`unsupported`, `vat_category_o_split_required` (EN 16931 BR-O-11 to BR-O-14).
Issue two documents.

### Overseas collectivities and the TAAF

Saint-Pierre-et-Miquelon (`PM`), Saint-Barthélemy (`BL`), Saint-Martin (`MF`),
French Polynesia (`PF`), New Caledonia (`NC`), Wallis-and-Futuna (`WF`) and the
TAAF (`TF`) are not part of France for VAT (CGI art. 256-0). Each legislates its
own indirect taxation, and no answer is deduced from a neighbour.

**Buyer established in one of the seven.** For an operation *located* in the
collectivity, French VAT is out of scope: the line is category `O` at 0, the
local tax is separate from French VAT. Cases settled by a collectivity's text
stay `final` under both sources: New Caledonia where the taxable buyer accounts
for the tax (art. Lp. 507-1), Saint-Barthélemy, Saint-Pierre-et-Miquelon, and
goods shipped to Saint-Martin.

Unmodelled local taxes are `unsupported` under `facturino`. Under `integration`
they are `final`, with a notice carrying the same code and
`foreignTaxReviewRequired: True`; the integrator declares and assumes the tax.

| Code | Unmodelled case |
|---|---|
| `com_taaf_local_tax_not_determined` | Non-taxable buyer (electronically supplied service to a consumer, CGI art. 259 D): a consumer self-assesses nothing, only the supplier could be called on to collect the collectivity's tax. |
| `com_taaf_local_regime_not_sourced` | Wallis-and-Futuna, TAAF: no official act held states who bears the tax. |
| `com_taaf_payment_withholding_not_modelled` | French Polynesia: the client withholds 10 % at source on the payment, and the service is taxed locally there. |

**Saint-Martin TGCA, under both sources.** A registration in force in
`sellerProfile["localTaxRegistrations"]` gives 4% per line in `localTax`;
a declared `localTaxExemption` (`cgism_253`, `not_used_in_saint_martin`) gives
0 with the mention. Without either, the decision is `pending_verification`
(`com_taaf_supplier_local_tax_liable`). `totals["totalLocalTax"]` is included in
`totalTTC` and the amount to collect. TGCA is separate from French VAT.

A general service to a consumer established in Saint-Martin without
`localTaxExemption` is an unmodelled cumulation of French VAT and TGCA:
`com_taaf_local_regime_not_sourced`,
`detailCode: french_vat_and_tgca_cumulation`. It is `unsupported` under
`facturino`, and `final` under `integration` with the notice and
`foreignTaxReviewRequired: True`.

**Seller established in one of the seven.** The decision is **not final**
(`unsupported`), with the *issue* `seller_com_taaf_local_tax_not_determined`: the
local tax of its collectivity decides what it invoices, and that is outside the
perimeter. This one is an issue, not a notice.

Under the `integration` source, a positive French VAT rate on a line located in
a collectivity answers `422 integration_vat_incoherent`: only
category `O` at 0 (`VATEX-EU-O`) describes such a place, and a positive rate
would declare a local tax as French VAT. `place_of_supply` is **required** on
every line as soon as the buyer is established in one of the seven — the place of
the operation is what says whether the local tax is at stake, and it is never
assumed (`422 integration_vat_incoherent` otherwise) — and it must be the place
Facturino decides. A place located in France (goods that never leave the
territory, a general B2C service) follows the French VAT rules; the Saint-Martin
cumulation above still requires its local-tax treatment.

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
paying a tax, not a rule of place. Without it and without a local registration,
the tax due at destination is still due: it is invoiced exactly as with the
one-stop shop (same rate, same lines, same axes), and the notice
`destination_mechanism_missing` says how to register in time. It never falls back
on the seller's own national VAT.

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

A missing threshold or location fact leaves `pending_verification`, without
amounts, with the fact and remedy in `issues`. Both sources refuse an EU address
missing the postal code needed to distinguish VAT territories.

| Issue code | What to complete |
| --- | --- |
| `eu_threshold_state_missing` | The EUR 10,000 threshold is not declared. Open the year's ledger; no origin taxation is presumed. |
| `destination_regional_scope_undetermined` | The address lacks the postal code needed to distinguish VAT territories. Supply it. |
| `location_evidence_contradictory`, `location_evidence_insufficient` | Supply enough concordant location evidence to establish the consumer's territory (art. 24b). |
| `location_evidence_relief_undetermined` | The art. 24b relaxation cannot be established. Open the year's ledger and declare the services figures, or supply a second item of evidence. |

`destination_mechanism_missing` is a notice on a `final` decision: destination
VAT is due and invoiced without a Union scheme or local registration valid for
that state on that date. Its `detailCode` (`threshold_exceeded`,
`destination_option` or `multi_member_state_establishment`) names the operation
that starts the registration period. Register with the one-stop shop by the
10th of the following month for it to apply from that operation (Implementing
Regulation (EU) 282/2011 art. 57 quinquies), or register in the member state.
A retained consumer territory can also carry a notice when two concordant
items of different kinds establish it, or every possible territory gives the
same complete tax result. Neither notice supplies a missing fact.

The following issues also keep the decision **non final**, without amounts.

| Issue code | When |
| --- | --- |
| `eu_threshold_external_coverage_incomplete` | Other channels exist and are not declared complete through the operation date. Record an adjustment — even a zero one, which simply states that nothing happened. |
| `eu_threshold_backdated_operation` | The operation predates one already counted, and decisions were frozen on that running total. It is refused rather than silently recomputed. |
| `eu_threshold_concurrent_decision_pending` | Other operations of the company are being decided at this very moment, and the cap falls between "all of them confirmed" and "all abandoned". Nothing is frozen on that: decide again once they conclude. |
| `eu_threshold_review_required` | The ledger is under review — its running total is known to be wrong, and no verdict rests on it until the review is settled. |
| `destination_threshold_operation_value_missing` | A line value cannot be sized, so no slice of the total can be taken for it. |
| `destination_threshold_price_mode_ambiguous` | Tax-inclusive price: the VAT-exclusive value depends on the rate the threshold has to decide, and the bounds fall on both sides of the cap. |
| `destination_option_period_invalid` | The option is declared over less than its minimum binding period. |
| `destination_option_scope_not_sourced` | Seller established outside France: the binding period is fixed by the member state where the option is exercised, and only the French one is sourced here. |
| `destination_establishment_in_member_state` | The seller declares an establishment in the destination member state: which establishment supplies then decides both the place and the mechanism, and no fact of the contract names it. A local VAT registration alone is not an establishment. |
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
  16% (CIVA art. 18, CTT postal ranges). An address placing no region at all does
  not block the decision: the mainland (`PT-CO`, 23%) is retained, with the notice
  `destination_regional_scope_undetermined`, which names it and asks for the
  postal code;
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
- a missing fact — `pending_verification` under both sources, without amounts.
  An unmodelled case is `unsupported` under `facturino`; under `integration`,
  it stays `final` with a notice carrying the same code and
  `foreignTaxReviewRequired: True`, and the integrator declares and assumes the tax.

The confrontation reaches BOTH places the rule can settle, and the territorial
frontier is shared too: a seller established outside the French VAT territory
raises under `integration` exactly the obstacle it raises under `facturino` (the
decision is `unsupported`). A buyer established in a territory excluded from
the EU VAT territory (the Canary Islands, Ceuta, Melilla, Åland…) is an unmodelled
case: `eu_special_territory_not_implemented`, refused under `facturino` and
carried as a notice on a `final` decision under `integration`, with
`foreignTaxReviewRequired: True`. The same distinction applies to goods
dispatched to another member state or XI for a non-taxable legal person that
communicated a VAT number
(`non_taxable_legal_person_goods_regime_not_modelled`). Both sources refuse a
document mixing category `O` with any other category
(`vat_category_o_split_required`; issue two documents), or an EU address missing
the postal code needed to distinguish VAT territories
(`destination_regional_scope_undetermined`).

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

## E-Reporting Declarations

Declarations returned by `client.ereporting` may include these read-only fields,
described by the exported `EReporting` response type:

| Field | Meaning |
|---|---|
| `obligationBasis` | Frozen transmission basis: `legal` for a legal obligation, `voluntary_early_adoption` for the seller's voluntary early adoption, or `None` when no obligation applies or the basis is unresolved. |
| `obligationDueFrom` | Legal opening date of the seller's wave, as `YYYY-MM-DD`, frozen at reservation; `None` if unresolved. A batch spanning several waves retains the earliest date. |
| `acknowledgedBy` | Identified acknowledgement author: `administration` (PPF), `platform` or `None` without an identified acknowledgement. This is independent of acceptance. |
| `skippedReason` | Non-transmission reason: `nothing_to_declare` with `state: skipped` means local closure without transmission and `obligation.state: completed`, for payments outside French VAT scope with no payment data expected. Open string or `None`. |

Each field may be `None` or absent on historical declarations. Read these
values from responses; they are not declaration inputs. The API contract date
remains `2026-09-01`.

The summary `status: skipped` alone does not establish local closure: it can
also summarize a `blocked` declaration whose obligation remains due. Read
`state`, `skippedReason` and `obligation` together; `state` remains an open string.

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
- **Same key + different body** — `409 conflict`. A key belongs to a
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
