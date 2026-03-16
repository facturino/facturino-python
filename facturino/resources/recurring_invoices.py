"""Recurring invoices resource — /v1/recurring-invoices

CRUD + activate (resume) / deactivate (pause).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class RecurringInvoices:
    """Synchronous recurring invoices resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a recurring invoice schedule.

        Args:
            customer_id / customerId: Customer ID.
            frequency: "monthly", "quarterly", "yearly", or "custom".
            start_date / startDate: ISO date for first generation.
            next_generation_date / nextGenerationDate: Next scheduled date.
            template_invoice / templateInvoice: Template data for generated invoices.
            auto_finalize / autoFinalize: Auto-finalize generated invoices.
            auto_send / autoSend: Auto-send generated invoices to PA.
            end_date / endDate: Optional end date.
        """
        body = dict(params)
        for snake, camel in [
            ("customer_id", "customerId"),
            ("start_date", "startDate"),
            ("next_generation_date", "nextGenerationDate"),
            ("end_date", "endDate"),
            ("template_invoice", "templateInvoice"),
            ("auto_finalize", "autoFinalize"),
            ("auto_send", "autoSend"),
        ]:
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = self._client.post("/v1/recurring-invoices", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        resp = self._client.get("/v1/recurring-invoices", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, recurring_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/recurring-invoices/{recurring_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, recurring_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        for snake, camel in [
            ("end_date", "endDate"),
            ("template_invoice", "templateInvoice"),
            ("auto_finalize", "autoFinalize"),
            ("auto_send", "autoSend"),
        ]:
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = self._client.patch(f"/v1/recurring-invoices/{recurring_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, recurring_id: str) -> None:
        self._client.delete(f"/v1/recurring-invoices/{recurring_id}")

    def activate(self, recurring_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/recurring-invoices/{recurring_id}/resume")
        return resp.json()  # type: ignore[no-any-return]

    def deactivate(self, recurring_id: str) -> dict[str, Any]:
        resp = self._client.post(f"/v1/recurring-invoices/{recurring_id}/pause")
        return resp.json()  # type: ignore[no-any-return]


class AsyncRecurringInvoices:
    """Asynchronous recurring invoices resource.

    CRUD + activate (resume) / deactivate (pause).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a recurring invoice schedule.

        Args:
            customer_id / customerId: Customer ID.
            frequency: "monthly", "quarterly", "yearly", or "custom".
            start_date / startDate: ISO date for first generation.
            next_generation_date / nextGenerationDate: Next scheduled date.
            template_invoice / templateInvoice: Template data for generated invoices.
            auto_finalize / autoFinalize: Auto-finalize generated invoices.
            auto_send / autoSend: Auto-send generated invoices to PA.
            end_date / endDate: Optional end date.
        """
        body = dict(params)
        for snake, camel in [
            ("customer_id", "customerId"),
            ("start_date", "startDate"),
            ("next_generation_date", "nextGenerationDate"),
            ("end_date", "endDate"),
            ("template_invoice", "templateInvoice"),
            ("auto_finalize", "autoFinalize"),
            ("auto_send", "autoSend"),
        ]:
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = await self._client.post("/v1/recurring-invoices", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/recurring-invoices", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, recurring_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/recurring-invoices/{recurring_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, recurring_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        for snake, camel in [
            ("end_date", "endDate"),
            ("template_invoice", "templateInvoice"),
            ("auto_finalize", "autoFinalize"),
            ("auto_send", "autoSend"),
        ]:
            if snake in body and camel not in body:
                body[camel] = body.pop(snake)
        resp = await self._client.patch(f"/v1/recurring-invoices/{recurring_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, recurring_id: str) -> None:
        await self._client.delete(f"/v1/recurring-invoices/{recurring_id}")

    async def activate(self, recurring_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/recurring-invoices/{recurring_id}/resume")
        return resp.json()  # type: ignore[no-any-return]

    async def deactivate(self, recurring_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/v1/recurring-invoices/{recurring_id}/pause")
        return resp.json()  # type: ignore[no-any-return]
