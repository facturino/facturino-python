"""Type definitions for Facturino API request and response objects.

All TypedDicts are provided for editor autocompletion. At runtime, the SDK
returns plain dicts (or FacturinoObject wrappers) so callers are not forced
to depend on these types.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

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
    vatCode: str
    # Optional specific VATEX exemption code (BT-121), e.g. "VATEX-FR-261",
    # when the exemption basis differs from the VAT category default.
    vatexCode: str
    discount_percent: int
    unit: str


class Totals(TypedDict, total=False):
    totalHT: str
    totalTVA: str
    totalTTC: str
    amountPaid: str
    amountDue: str


class LifecycleEntry(TypedDict, total=False):
    code: str
    params: dict[str, str | int | float]
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


class LegalFormInput(TypedDict, total=False):
    """Legal-form input for company/customer create/update.

    Provide either the 4-digit INSEE ``code`` or the ``sigle`` (e.g. "SAS");
    the API resolves the canonical object. Do not send ``label`` — the input
    is strictly validated and unknown keys are rejected.
    """

    code: str
    sigle: str


class NafInput(TypedDict, total=False):
    """NAF (APE) input. Provide the Rev. 2 ``code`` (e.g. "62.01Z" or "6201Z")."""

    code: str


class CustomerCreateParams(TypedDict, total=False):
    name: str
    type: str
    email: str
    siret: str
    siren: str
    vatNumber: str
    vat_number: str
    legalForm: LegalFormInput
    naf: NafInput
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
    legalForm: LegalFormInput
    naf: NafInput
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
# Exports
# ---------------------------------------------------------------------------


class FecExportParams(TypedDict, total=False):
    period_start: str
    period_end: str
    send_to_accountant: bool
    accountant_email: str


class InvoiceExportParams(TypedDict, total=False):
    period_start: str
    period_end: str
    statuses: list[str]


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


# Response models keep additive/legacy fields optional. Runtime values stay dicts.

PaRejectionCategory = Literal[
    "buyer_not_in_directory",
    "addressing_error",
    "other",
    "format_invalid",
    "semantic_error",
    "duplicate",
    "platform_auth",
    "platform_unavailable",
    "refused_by_buyer",
    "suspended",
    "unknown",
]
PaRejectionSource = Literal["platform", "buyer", "facturino"]


class InvoiceSubmissionArtefact(TypedDict, total=False):
    kind: Literal["cii"]
    path: str
    generatedAt: str
    correctedRules: list[str]
    routingIdentifier: str


class InvoicePreviousSubmission(TypedDict, total=False):
    paId: str | None
    paTransactionId: str | None
    paIdempotencyKey: str | None
    paStatus: str | None
    paStatusCode: str | None
    paErrorCode: str | None
    rejectionReason: str | None
    rejectionCategory: PaRejectionCategory | None
    sentAt: str | None
    closedAt: str
    rejectionCode: str | None
    rejectionSource: PaRejectionSource | None
    rejectionNote: str | None


class InvoiceEinvoicing(TypedDict, total=False):
    paId: str | None
    paStatus: str | None
    paStatusCode: str | None
    paTransactionId: str | None
    paErrorCode: str | None
    rejectionReason: str | None
    rejectionCategory: PaRejectionCategory | None
    refusalReason: str | None
    paIdempotencyKey: str | None
    peppolDeliveryId: str | None
    ereportingId: str | None
    sentAt: str | None
    trackingId: str | None
    submissionArtefact: InvoiceSubmissionArtefact | None
    previousSubmissions: list[InvoicePreviousSubmission]
    rejectionCode: str | None
    rejectionSource: PaRejectionSource | None
    rejectionNote: str | None
    routingIdentifier: str | None
    buyerReachableAt: str | None
    directoryCheckedAt: str | None
    ereportingPaymentId: str | None


class CreditNoteEinvoicing(TypedDict, total=False):
    paErrorCode: str | None
    paStatusCode: str | None
    rejectionCode: str | None
    rejectionSource: PaRejectionSource | None
    rejectionReason: str | None
    rejectionNote: str | None
    rejectionCategory: PaRejectionCategory | None
    previousSubmissions: list[InvoicePreviousSubmission]
    paId: str | None
    paStatus: str | None
    depositedAt: str | None
    paIdempotencyKey: str
    ereportingId: str | None


class PaymentCollectionStatus(TypedDict, total=False):
    state: Literal["pending", "awaiting_deposit", "sent", "blocked", "reconciliation_required", "failed"]
    sentAt: str | None
    lastErrorCode: str | None
    lastErrorReason: str
    updatedAt: str


class BuyerNatureWarning(TypedDict, total=False):
    code: Literal["buyer_nature_suspect"]
    message: str
    param: str


class Invoice(TypedDict, total=False):
    paymentInfo: dict[str, Any]
    archive: dict[str, Any] | None
    portal: dict[str, Any] | None
    legalMentions: str | None
    purchaseOrderNumber: str | None
    reminderTaskIds: list[Any]
    processed: bool
    anonymized: bool
    anonymizedAt: str | None
    metadata: dict[str, Any]
    id: str
    object: str
    type: Literal["standard", "deposit", "corrective", "self_billing"]
    status: Literal[
        "draft",
        "finalized",
        "sending",
        "deposited",
        "transmitted",
        "rejected",
        "available",
        "received",
        "approved",
        "refused",
        "suspended",
        "partially_paid",
        "paid",
        "overdue",
    ]
    number: str | None
    currency: str
    customer: dict[str, Any]
    items: list[LineItem]
    totals: Totals
    dates: dict[str, Any]
    deposits: list[dict[str, Any]]
    paymentSchedule: list[dict[str, Any]]
    notes: str | None
    livemode: bool
    created: str
    updated: str
    taxDecisionId: str
    taxSource: Literal["facturino", "integration"]
    commercialDraft: dict[str, Any] | None
    taxSnapshot: dict[str, Any]
    documentStatus: Literal["draft", "finalized", "cancelled"]
    transmissionStatus: Literal[
        "not_applicable", "pending", "sending", "deposited", "transmitted", "approved", "rejected"
    ]
    transmissionDetail: Literal["available", "received", "suspended", "refused"] | None
    paymentStatus: Literal["unpaid", "partially_paid", "paid", "partially_refunded", "refunded"]
    einvoicing: InvoiceEinvoicing
    files: dict[str, Any]
    lifecycle: list[LifecycleEntry]


class Payment(TypedDict, total=False):
    companyId: str
    invoiceId: str
    livemode: bool
    creditNoteId: str
    cancelledAt: str
    id: str
    object: str
    type: Literal["payment", "refund"]
    status: Literal["cancelled"] | None
    amount: int
    method: Literal["transfer", "card", "check", "cash", "direct_debit", "sepa", "paypal", "other"]
    reference: str | None
    paidAt: str
    recorded_by: Literal["api", "app", "system"]
    created: str
    fr212: PaymentCollectionStatus | None


class Customer(TypedDict, total=False):
    companyId: str
    balance: int
    currency: str
    siretVerified: bool
    vatVerified: bool
    id: str
    object: str
    warnings: list[BuyerNatureWarning]
    name: str
    type: Literal["company", "individual"]
    siret: str | None
    vatNumber: str | None
    legalForm: dict[str, Any]
    naf: dict[str, Any]
    address: Address
    deliveryAddress: Address
    contacts: list[dict[str, Any]]
    active: bool
    livemode: bool
    created: str
    updated: str


class TaxDecision(TypedDict, total=False):
    warnings: list[BuyerNatureWarning]
    id: str
    object: Literal["tax_decision"]
    taxSource: Literal["facturino", "integration"]
    companyId: str
    status: Literal["final", "pending_verification", "unsupported"]
    customerId: str
    customer: dict[str, Any]
    sellerProfileId: str
    sellerProfileRevision: int
    sellerProfile: dict[str, Any]
    currency: str
    priceMode: Literal["tax_exclusive", "tax_inclusive"]
    effectiveAt: str
    decidedAt: str
    expiresAt: str
    checkoutValidityPolicy: Literal["checkout-validity-v1"]
    expired: bool
    rulesVersion: str
    reportingCalendar: str
    roundingPolicy: str
    requestFingerprint: str
    operationFingerprint: str
    lines: list[dict[str, Any]]
    totals: dict[str, Any] | None
    vatBreakdown: list[dict[str, Any]]
    amountToCharge: int | None
    invoiceChannel: Literal["einvoicing", "none"] | None
    transactionReporting: Literal["ereporting", "none", "outside_scope"] | None
    paymentReporting: Literal["fr212", "ereporting", "none"] | None
    settledObligations: dict[str, Any] | None
    euB2cDestination: dict[str, Any] | None
    foreignTaxReviewRequired: bool
    vies: dict[str, Any]
    locationEvidence: list[dict[str, Any]]
    nonEuBusinessEvidence: dict[str, Any] | None
    issues: list[dict[str, Any]]
    obligationReasons: list[dict[str, Any]]
    retryOfTaxDecisionId: str | None
    livemode: bool
    created: str
    updated: str


class CreditNote(TypedDict, total=False):
    companyId: str
    customer: dict[str, Any]
    currency: str
    reason: str
    dates: dict[str, Any]
    archive: dict[str, Any] | None
    lifecycle: list[Any]
    processed: bool
    updated: str
    id: str
    object: str
    status: Literal["draft", "finalized", "credit_deposited", "credit_transmitted", "credit_approved", "credit_refused"]
    number: str | None
    relatedInvoiceId: str
    relatedInvoiceNumber: str | None
    creditNoteType: str
    reasonCode: Literal["defective_goods", "duplicate", "quality", "other"]
    items: list[LineItem]
    totals: Totals
    livemode: bool
    created: str
    originalInvoiceId: str
    originalTaxDecisionId: str
    taxSource: Literal["facturino", "integration"]
    taxSnapshot: dict[str, Any]
    documentStatus: Literal["draft", "finalized", "cancelled"]
    transmissionStatus: Literal[
        "not_applicable", "pending", "sending", "deposited", "transmitted", "approved", "rejected"
    ]
    transmissionDetail: Literal["available", "received", "suspended", "refused"] | None
    paymentStatus: Literal["unpaid", "partially_paid", "paid", "partially_refunded", "refunded"]
    einvoicing: CreditNoteEinvoicing


class WebhookEventData(TypedDict, total=False):
    paStatus: str
    paInvoiceId: str | None
    invoiceId: str
    paymentId: str
    method: str
    pa_invoice_id: str
    sender_siret: str
    sender_name: str
    total_ht: str
    total_tva: str
    total_ttc: str
    recurringInvoiceId: str
    error: str
    count: int
    plan: str
    stripeSubscriptionId: str
    reason: str
    attempt: int
    pausedUntil: str | None
    period: str | None
    type: str | None

    id: str
    object: str
    status: str
    previous_status: str
    livemode: bool
    number: str | None
    documentStatus: Literal["draft", "finalized", "cancelled"]
    transmissionStatus: Literal[
        "not_applicable", "pending", "sending", "deposited", "transmitted", "approved", "rejected"
    ]
    transmissionDetail: Literal["available", "received", "suspended", "refused"] | None
    paymentStatus: Literal["unpaid", "partially_paid", "paid", "partially_refunded", "refunded"]
    paErrorCode: str | None
    rejectionReason: str | None
    rejectionCategory: PaRejectionCategory | None
    rejectionCode: str | None
    rejectionSource: PaRejectionSource | None
    relatedInvoiceId: str | None
    relatedInvoiceNumber: str | None
    metadata: dict[str, Any]
    amount: str
    total_paid: str
    total_due: str
    total: str
    amountDue: str


class WebhookAttempt(TypedDict, total=False):
    timestamp: str
    httpStatus: int | None
    error: str
    duration: float
    endpointId: str


class EndpointDelivery(TypedDict, total=False):
    attemptCount: int
    generation: int
    delivered: bool
    attempts: list[WebhookAttempt]
    nextRetry: str | None


class WebhookEvent(TypedDict, total=False):
    id: str
    object: Literal["event"]
    type: str
    apiVersion: str
    data: WebhookEventData
    request: dict[str, Any] | None
    livemode: bool
    created: str
    updated: str
    companyId: str
    endpointId: str
    delivered: bool
    attempts: list[WebhookAttempt]
    nextRetry: str | None
    deliveries: dict[str, Any]
    expireAt: str


class EventRetryResult(TypedDict, total=False):
    id: str
    object: Literal["event"]
    retryScheduled: bool
    endpointId: str
