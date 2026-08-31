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

**Immediate collection** — capture the decided amount, verify, then finalize:

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

client.invoices.finalize(invoice["id"])

# Record the REAL payment — its real date, method and the settlement's
# financial reference (never the decision id).
client.payments.create(
    invoice["id"],
    amount=settlement["amount"],
    # transfer, card, check, cash, direct_debit, sepa, paypal or other
    method=settlement["method"],
    reference=settlement["reference"],
    paidAt=settlement["paidAt"],
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
