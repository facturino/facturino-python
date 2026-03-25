"""Facturino Python SDK — developer-first e-invoicing for France.

Usage::

    import facturino

    client = facturino.Client("fac_test_xxx")

    # Create a customer
    customer = client.customers.create(
        name="ACME Corp",
        type="company",
        email="billing@acme.com",
        siret="12345678901234",
    )

    # Create and finalize an invoice
    invoice = client.invoices.create(
        customer=customer["id"],
        items=[{
            "description": "Consulting",
            "quantity": 1,
            "unit_price": 10000,
            "vat_rate": 2000,
        }],
    )
    finalized = client.invoices.finalize(invoice["id"])

    # Auto-pagination
    for inv in client.invoices.list(limit=10):
        print(inv["id"], inv["status"])

    # Webhook verification
    event = facturino.Webhook.construct_event(payload, signature, secret)

Async usage::

    async_client = facturino.AsyncClient("fac_test_xxx")

    invoice = await async_client.invoices.create(customer="cus_xxx", items=[...])

    async for inv in await async_client.invoices.list():
        print(inv["id"])
"""

from __future__ import annotations

from ._client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, MAX_RETRIES, VERSION, AsyncHttpClient, SyncHttpClient
from ._errors import (
    ApiError,
    AuthenticationError,
    ConflictError,
    FacturinoError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    PlanLimitError,
    RateLimitError,
    ServerError,
    SignatureVerificationError,
    ValidationError,
)
from ._pagination import AsyncPage, SyncPage
from ._webhooks import Webhook
from .resources.api_keys import ApiKeys, AsyncApiKeys
from .resources.companies import AsyncCompanies, Companies
from .resources.credit_notes import AsyncCreditNotes, CreditNotes
from .resources.customers import AsyncCustomers, Customers
from .resources.ereporting import AsyncEreporting, Ereporting
from .resources.events import AsyncEvents, Events
from .resources.exports import AsyncExports, Exports
from .resources.invoices import AsyncInvoices, Invoices
from .resources.jobs import AsyncJobs, Jobs
from .resources.members import AsyncMembers, Members
from .resources.mfa import AsyncMfa, Mfa
from .resources.payments import AsyncPayments, Payments
from .resources.products import AsyncProducts, Products
from .resources.quotes import AsyncQuotes, Quotes
from .resources.received_invoices import AsyncReceivedInvoices, ReceivedInvoices
from .resources.recurring_invoices import AsyncRecurringInvoices, RecurringInvoices
from .resources.reporting import AsyncReporting, Reporting
from .resources.sandbox import AsyncSandbox, Sandbox
from .resources.webhook_endpoints import AsyncWebhookEndpoints, WebhookEndpoints

__version__ = VERSION

__all__ = [
    # Clients
    "Client",
    "AsyncClient",
    # Webhook utility
    "Webhook",
    # Pagination
    "SyncPage",
    "AsyncPage",
    # Errors
    "FacturinoError",
    "ApiError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "InvalidRequestError",
    "ValidationError",
    "PlanLimitError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "SignatureVerificationError",
    # Version
    "__version__",
]


class Client:
    """Synchronous Facturino API client.

    Args:
        api_key: Your Facturino API key (``fac_test_xxx`` or ``fac_live_xxx``).
        base_url: API base URL. Defaults to ``https://facturino.com/api``.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts on transient failures. Defaults to 3.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise FacturinoError(
                "API key is required. Pass your key as: facturino.Client('fac_test_xxx')"
            )

        self._http = SyncHttpClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Resource namespaces
        self.invoices = Invoices(self._http)
        self.payments = Payments(self._http)
        self.customers = Customers(self._http)
        self.products = Products(self._http)
        self.quotes = Quotes(self._http)
        self.credit_notes = CreditNotes(self._http)
        self.events = Events(self._http)
        self.webhook_endpoints = WebhookEndpoints(self._http)
        self.recurring_invoices = RecurringInvoices(self._http)
        self.received_invoices = ReceivedInvoices(self._http)
        self.companies = Companies(self._http)
        self.members = Members(self._http)
        self.api_keys = ApiKeys(self._http)
        self.exports = Exports(self._http)
        self.ereporting = Ereporting(self._http)
        self.reporting = Reporting(self._http)
        self.mfa = Mfa(self._http)
        self.jobs = Jobs(self._http)
        self.sandbox = Sandbox(self._http)

    def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        key_preview = self._http.api_key[:12] + "..." if len(self._http.api_key) > 12 else "***"
        return f"facturino.Client(api_key={key_preview!r})"


class AsyncClient:
    """Asynchronous Facturino API client.

    Usage::

        async with facturino.AsyncClient("fac_test_xxx") as client:
            invoice = await client.invoices.create(...)

    Args:
        api_key: Your Facturino API key.
        base_url: API base URL. Defaults to ``https://facturino.com/api``.
        timeout: Request timeout in seconds. Defaults to 30.
        max_retries: Maximum retry attempts on transient failures. Defaults to 3.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise FacturinoError(
                "API key is required. Pass your key as: facturino.AsyncClient('fac_test_xxx')"
            )

        self._http = AsyncHttpClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Resource namespaces
        self.invoices = AsyncInvoices(self._http)
        self.payments = AsyncPayments(self._http)
        self.customers = AsyncCustomers(self._http)
        self.products = AsyncProducts(self._http)
        self.quotes = AsyncQuotes(self._http)
        self.credit_notes = AsyncCreditNotes(self._http)
        self.events = AsyncEvents(self._http)
        self.webhook_endpoints = AsyncWebhookEndpoints(self._http)
        self.recurring_invoices = AsyncRecurringInvoices(self._http)
        self.received_invoices = AsyncReceivedInvoices(self._http)
        self.companies = AsyncCompanies(self._http)
        self.members = AsyncMembers(self._http)
        self.api_keys = AsyncApiKeys(self._http)
        self.exports = AsyncExports(self._http)
        self.ereporting = AsyncEreporting(self._http)
        self.reporting = AsyncReporting(self._http)
        self.mfa = AsyncMfa(self._http)
        self.jobs = AsyncJobs(self._http)
        self.sandbox = AsyncSandbox(self._http)

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._http.close()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def __repr__(self) -> str:
        key_preview = self._http.api_key[:12] + "..." if len(self._http.api_key) > 12 else "***"
        return f"facturino.AsyncClient(api_key={key_preview!r})"
