"""Facturino API resource modules."""

from .archives import Archives, AsyncArchives
from .companies import AsyncCompanies, Companies
from .credit_notes import AsyncCreditNotes, CreditNotes
from .customers import AsyncCustomers, Customers
from .ereporting import AsyncEreporting, Ereporting
from .events import AsyncEvents, Events
from .exports import AsyncExports, Exports
from .health import AsyncHealth, Health
from .invoices import AsyncInvoices, Invoices
from .jobs import AsyncJobs, Jobs
from .payments import AsyncPayments, Payments
from .products import AsyncProducts, Products
from .quotes import AsyncQuotes, Quotes
from .received_invoices import AsyncReceivedInvoices, ReceivedInvoices
from .recurring_invoices import AsyncRecurringInvoices, RecurringInvoices
from .reporting import AsyncReporting, Reporting
from .sandbox import AsyncSandbox, Sandbox
from .tax_decisions import AsyncTaxDecisions, TaxDecisions
from .webhook_endpoints import AsyncWebhookEndpoints, WebhookEndpoints

__all__ = [
    "Archives",
    "AsyncArchives",
    "Companies",
    "AsyncCompanies",
    "CreditNotes",
    "AsyncCreditNotes",
    "Customers",
    "AsyncCustomers",
    "Ereporting",
    "AsyncEreporting",
    "Events",
    "AsyncEvents",
    "Exports",
    "AsyncExports",
    "Health",
    "AsyncHealth",
    "Invoices",
    "AsyncInvoices",
    "Jobs",
    "AsyncJobs",
    "Payments",
    "AsyncPayments",
    "Products",
    "AsyncProducts",
    "Quotes",
    "AsyncQuotes",
    "ReceivedInvoices",
    "AsyncReceivedInvoices",
    "RecurringInvoices",
    "AsyncRecurringInvoices",
    "Reporting",
    "AsyncReporting",
    "Sandbox",
    "AsyncSandbox",
    "TaxDecisions",
    "AsyncTaxDecisions",
    "WebhookEndpoints",
    "AsyncWebhookEndpoints",
]
