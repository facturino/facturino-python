# Facturino Python SDK

Official Python client library for the [Facturino API](https://facturino.com/docs/api) — developer-first e-invoicing for France.

[![PyPI version](https://img.shields.io/pypi/v/facturino.svg)](https://pypi.org/project/facturino/)
[![Python versions](https://img.shields.io/pypi/pyversions/facturino.svg)](https://pypi.org/project/facturino/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install facturino
```

Requires Python 3.9+.

## Quick Start

```python
import facturino

client = facturino.Client("fac_test_xxx")

# Create a customer
customer = client.customers.create(
    name="ACME Corp",
    type="company",
    email="billing@acme.com",
    siret="73282932000074",
    address={"line1": "10 rue de la Paix", "postalCode": "75002", "city": "Paris", "country": "FR"},
)

# Create a draft invoice
invoice = client.invoices.create(
    customer=customer["id"],
    buyer={
        "companyName": "Acme SAS",
        "siret": "55208131766522",
        "address": {"line1": "10 rue de la Paix", "postalCode": "75002", "city": "Paris", "country": "FR"},
    },
    items=[{
        "description": "Consulting services",
        "quantity": "1",           # decimal string
        "unit": "flat_rate",
        "unitPrice": 10000,        # 100.00 EUR (integer centimes)
        "vatRate": 2000,           # 20.00% (integer centipercent)
        "vatCode": "S",
    }],
    dates={"issued": "2026-07-01", "due": "2026-07-31"},
    payment={"terms": "Paiement à 30 jours", "termsDays": 30, "method": "transfer", "latePaymentRate": "10.00", "collectionFee": "40.00"},
)

# Finalize the invoice (assigns number, locks editing)
finalized = client.invoices.finalize(invoice["id"])
print(f"Invoice {finalized['number']} finalized")

# Send to the e-invoicing platform (PA)
client.invoices.send(finalized["id"])

# One-shot alternative — finalize (and optionally deliver) in the create call:
#   client.invoices.create(..., autoFinalize=True,
#                          autoSend={"email": True, "pa": True})
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
        invoice = await client.invoices.create(
            customer="cus_xxx",
            buyer={"companyName": "Acme SAS", "siret": "55208131766522",
                   "address": {"line1": "10 rue de la Paix", "postalCode": "75002", "city": "Paris", "country": "FR"}},
            items=[{"description": "Widget", "quantity": "2", "unit": "unit", "unitPrice": 5000, "vatRate": 2000, "vatCode": "S"}],
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
| `client.invoices` | `create`, `list`, `get`, `update`, `delete`, `finalize`, `send`, `cancel`, `remind`, `clone`, `get_pdf`, `get_facturx`, `get_xml`, `get_status`, `verify`, `list_events`, `get_audit_trail`, `generate_audit_trail_pdf`, `create_payment_link`, `create_payment_token` |
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

All POST requests automatically include an `Idempotency-Key` header (UUID v4). You can provide your own when creating resources:

```python
invoice = client.invoices.create(
    customer="cus_xxx",
    items=[...],
    idempotency_key="unique-request-id-123",
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
