"""Optional payload projections, keyed by the event type; runtime dictionaries retain every field."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class InvoiceWebhookData(TypedDict, total=False):
    id: str
    object: Literal["invoice"]
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
    rejectionCategory: (
        Literal[
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
        | None
    )
    rejectionCode: str | None
    rejectionSource: Literal["platform", "buyer", "facturino"] | None
    metadata: dict[str, Any]


class IncomingInvoiceWebhookData(TypedDict, total=False):
    id: str
    object: Literal["received_invoice"]
    pa_invoice_id: str
    sender_siret: str
    sender_name: str
    number: str | None
    total_ht: str
    total_tva: str
    total_ttc: str


class QuoteWebhookData(TypedDict, total=False):
    id: str
    object: Literal["quote"]
    status: str
    previous_status: str
    livemode: bool
    number: str | None
    metadata: dict[str, Any]


class CreditNoteWebhookData(TypedDict, total=False):
    paStatus: str
    paInvoiceId: str | None
    id: str
    object: Literal["credit_note"]
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
    rejectionCategory: (
        Literal[
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
        | None
    )
    rejectionCode: str | None
    rejectionSource: Literal["platform", "buyer", "facturino"] | None
    metadata: dict[str, Any]
    relatedInvoiceId: str | None
    relatedInvoiceNumber: str | None


class CustomerWebhookData(TypedDict, total=False):
    id: str
    object: Literal["customer"]
    livemode: bool


class PaymentCreatedWebhookData(TypedDict, total=False):
    invoiceId: str
    paymentId: str
    amount: str
    method: str


class PaymentReceivedWebhookData(TypedDict, total=False):
    id: str
    object: Literal["invoice"]
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
    rejectionCategory: (
        Literal[
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
        | None
    )
    rejectionCode: str | None
    rejectionSource: Literal["platform", "buyer", "facturino"] | None
    metadata: dict[str, Any]
    amount: str
    total_paid: str
    total_due: str
    total: str
    amountDue: str


class EreportingWebhookData(TypedDict, total=False):
    id: str
    object: Literal["ereporting"]
    status: str
    type: str | None
    period: str | None
    attempt: int


class RecurringGeneratedWebhookData(TypedDict, total=False):
    id: str
    object: Literal["invoice"]
    recurringInvoiceId: str
    livemode: bool


class RecurringFailedWebhookData(TypedDict, total=False):
    id: str
    object: Literal["recurring_invoice"]
    error: str


class ExportWebhookData(TypedDict, total=False):
    id: str
    object: Literal["export"]
    count: int


class SubscriptionWebhookData(TypedDict, total=False):
    plan: str
    status: str
    stripeSubscriptionId: str
    pausedUntil: str | None
    reason: str


EVENT_DATA_TYPES = {
    "invoice.created": InvoiceWebhookData,
    "invoice.finalized": InvoiceWebhookData,
    "invoice.sending": InvoiceWebhookData,
    "invoice.sent": InvoiceWebhookData,
    "invoice.deposited": InvoiceWebhookData,
    "invoice.transmitted": InvoiceWebhookData,
    "invoice.available": InvoiceWebhookData,
    "invoice.received": InvoiceWebhookData,
    "invoice.approved": InvoiceWebhookData,
    "invoice.refused": InvoiceWebhookData,
    "invoice.rejected": InvoiceWebhookData,
    "invoice.suspended": InvoiceWebhookData,
    "invoice.paid": InvoiceWebhookData,
    "invoice.partially_paid": InvoiceWebhookData,
    "invoice.overdue": InvoiceWebhookData,
    "invoice.incoming.received": IncomingInvoiceWebhookData,
    "quote.created": QuoteWebhookData,
    "quote.sent": QuoteWebhookData,
    "quote.viewed": QuoteWebhookData,
    "quote.accepted": QuoteWebhookData,
    "quote.refused": QuoteWebhookData,
    "quote.expired": QuoteWebhookData,
    "quote.converted": QuoteWebhookData,
    "credit_note.created": CreditNoteWebhookData,
    "credit_note.finalized": CreditNoteWebhookData,
    "credit_note.credit_deposited": CreditNoteWebhookData,
    "credit_note.credit_transmitted": CreditNoteWebhookData,
    "credit_note.credit_approved": CreditNoteWebhookData,
    "credit_note.credit_refused": CreditNoteWebhookData,
    "credit_note.sent": CreditNoteWebhookData,
    "customer.created": CustomerWebhookData,
    "customer.updated": CustomerWebhookData,
    "customer.deleted": CustomerWebhookData,
    "payment.created": PaymentCreatedWebhookData,
    "payment.received": PaymentReceivedWebhookData,
    "ereporting.submitted": EreportingWebhookData,
    "recurring_invoice.generated": RecurringGeneratedWebhookData,
    "recurring_invoice.failed": RecurringFailedWebhookData,
    "export.ready": ExportWebhookData,
    "subscription.created": SubscriptionWebhookData,
    "subscription.cancelled": SubscriptionWebhookData,
    "subscription.renewed": SubscriptionWebhookData,
    "subscription.paused": SubscriptionWebhookData,
}
