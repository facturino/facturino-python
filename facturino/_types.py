"""Type definitions for Facturino API request and response objects.

All TypedDicts are provided for editor autocompletion. At runtime, the SDK
returns plain dicts (or FacturinoObject wrappers) so callers are not forced
to depend on these types.
"""

from __future__ import annotations

from typing import Any, TypedDict

# ---------------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------------

class Address(TypedDict, total=False):
    line1: str
    line2: str
    postalCode: str
    city: str
    country: str


class CustomerSnapshot(TypedDict, total=False):
    name: str
    address: Address
    siret: str | None
    vatNumber: str | None


class CustomerRef(TypedDict, total=False):
    ref: str
    snapshot: CustomerSnapshot


class LineItem(TypedDict, total=False):
    product: str | None
    description: str
    quantity: int
    unit_price: int
    vat_rate: int
    discount_percent: int
    unit: str


class Totals(TypedDict, total=False):
    totalHT: str
    totalTVA: str
    totalTTC: str
    amountPaid: str
    amountDue: str


class LifecycleEntry(TypedDict, total=False):
    status: str
    timestamp: str
    source: str
    details: str | None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class ListParams(TypedDict, total=False):
    """Common query parameters for list endpoints."""
    limit: int
    starting_after: str
    ending_before: str
    status: str
    include_deleted: bool


class PaginatedResponse(TypedDict):
    """Shape of all paginated list responses."""
    object: str
    url: str
    data: list[dict[str, Any]]
    has_more: bool
    next_cursor: str | None


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

class InvoiceCreateParams(TypedDict, total=False):
    customer: str  # customer ID (mapped to customerId)
    items: list[LineItem]
    lines: list[LineItem]  # alias for items
    type: str
    dates: dict[str, str]
    payment: dict[str, Any]
    notes: str
    metadata: dict[str, Any]


class InvoiceUpdateParams(TypedDict, total=False):
    items: list[LineItem]
    lines: list[LineItem]
    dates: dict[str, str]
    payment: dict[str, Any]
    notes: str
    metadata: dict[str, Any]


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

class PaymentCreateParams(TypedDict, total=False):
    amount: int  # integer centimes
    method: str
    reference: str
    paidAt: str  # ISO 8601
    paid_at: str  # snake_case alias


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class CustomerCreateParams(TypedDict, total=False):
    name: str
    type: str
    email: str
    siret: str
    siren: str
    vatNumber: str
    vat_number: str
    legalForm: str
    nafCode: str
    address: Address
    deliveryAddress: Address
    contacts: list[dict[str, Any]]
    paymentTerms: int
    tags: list[str]
    notes: str
    paIdentifier: str
    preferredFormat: str
    receivingPaId: str


class CustomerUpdateParams(TypedDict, total=False):
    name: str
    email: str
    address: Address
    deliveryAddress: Address
    contacts: list[dict[str, Any]]
    paymentTerms: int
    tags: list[str]
    notes: str


class CustomerLookupParams(TypedDict, total=False):
    siret: str
    query: str


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class ProductCreateParams(TypedDict, total=False):
    name: str
    description: str
    reference: str
    category: str
    unitPrice: int
    unit_price: int
    vatRate: int
    vat_rate: int
    vatCode: str
    unit: str
    tags: list[str]


class ProductUpdateParams(TypedDict, total=False):
    name: str
    description: str
    reference: str
    category: str
    unitPrice: int
    unit_price: int
    vatRate: int
    vat_rate: int
    unit: str
    tags: list[str]


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

class QuoteCreateParams(TypedDict, total=False):
    customer: str
    items: list[LineItem]
    lines: list[LineItem]
    dates: dict[str, Any]
    notes: str


class QuoteUpdateParams(TypedDict, total=False):
    items: list[LineItem]
    lines: list[LineItem]
    dates: dict[str, Any]
    notes: str


# ---------------------------------------------------------------------------
# Credit Notes
# ---------------------------------------------------------------------------

class CreditNoteCreateParams(TypedDict, total=False):
    customer: str
    relatedInvoiceId: str
    related_invoice_id: str
    creditNoteType: str
    credit_note_type: str
    reasonCode: str
    reason_code: str
    reason: str
    items: list[LineItem]
    dates: dict[str, str]
    notes: str


class CreditNoteUpdateParams(TypedDict, total=False):
    items: list[LineItem]
    reason: str
    notes: str


# ---------------------------------------------------------------------------
# Webhook Endpoints
# ---------------------------------------------------------------------------

class WebhookEndpointCreateParams(TypedDict, total=False):
    url: str
    events: list[str]
    description: str


class WebhookEndpointUpdateParams(TypedDict, total=False):
    url: str
    events: list[str]
    description: str
    active: bool


# ---------------------------------------------------------------------------
# Recurring Invoices
# ---------------------------------------------------------------------------

class RecurringInvoiceCreateParams(TypedDict, total=False):
    customerId: str
    customer_id: str
    frequency: str
    customInterval: int
    customUnit: str
    startDate: str
    start_date: str
    nextGenerationDate: str
    next_generation_date: str
    endDate: str
    end_date: str
    templateInvoice: dict[str, Any]
    template_invoice: dict[str, Any]
    autoFinalize: bool
    auto_finalize: bool
    autoSend: bool
    auto_send: bool


class RecurringInvoiceUpdateParams(TypedDict, total=False):
    frequency: str
    customInterval: int
    customUnit: str
    endDate: str
    end_date: str
    templateInvoice: dict[str, Any]
    template_invoice: dict[str, Any]
    autoFinalize: bool
    auto_finalize: bool
    autoSend: bool
    auto_send: bool


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

class ApiKeyCreateParams(TypedDict, total=False):
    name: str
    permissions: list[str]


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

class MemberInviteParams(TypedDict, total=False):
    email: str
    role: str
    displayName: str
    display_name: str


class MemberUpdateParams(TypedDict, total=False):
    role: str


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

class FecExportParams(TypedDict, total=False):
    period_start: str
    period_end: str
    send_to_accountant: bool
    accountant_email: str


# ---------------------------------------------------------------------------
# E-Reporting
# ---------------------------------------------------------------------------

class EreportingLine(TypedDict, total=False):
    category: str
    amount: int
    vatRate: int
    vat_rate: int
    vatAmount: int
    vat_amount: int


class EreportingCreateParams(TypedDict, total=False):
    type: str
    period: str
    lines: list[EreportingLine]


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------

class SimulateStatusParams(TypedDict, total=False):
    status: str
