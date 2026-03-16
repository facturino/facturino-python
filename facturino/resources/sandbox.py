"""Sandbox resource — /v1/sandbox

Test-mode utilities: reset data, simulate PA status changes, create fixtures.
Only available with test API keys (fac_test_*).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Sandbox:
    """Synchronous sandbox resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def reset_data(self) -> dict[str, Any]:
        """Reset all test data and reload sandbox fixtures.

        Soft-deletes all test-mode resources (invoices, customers, products,
        quotes, credit notes, payments, recurring invoices) then reloads
        sandbox fixtures (5 customers, 10 products, 20 invoices).

        Only available with fac_test_* API keys.

        Returns:
            Dict with deleted_count and fixtures_created.
        """
        resp = self._client.post("/v1/sandbox/reset")
        return resp.json()  # type: ignore[no-any-return]

    def simulate_status(self, invoice_id: str, status: str) -> dict[str, Any]:
        """Simulate a PA status change on a test-mode invoice.

        This is useful for testing webhook handlers and status-dependent
        business logic without a real PA connection.

        Args:
            invoice_id: The invoice to update.
            status: Target status. Must be one of: deposited, transmitted,
                available, received, approved, refused, suspended, rejected,
                paid, partially_paid, overdue.

        Returns:
            Updated invoice dict with simulated=True.
        """
        resp = self._client.post(
            f"/v1/sandbox/simulate-status/{invoice_id}",
            json={"status": status},
        )
        return resp.json()  # type: ignore[no-any-return]

    def create_fixtures(self) -> dict[str, Any]:
        """Alias for reset_data."""
        return self.reset_data()


class AsyncSandbox:
    """Asynchronous sandbox resource.

    Test-mode utilities: reset data, simulate PA status changes, create fixtures.
    Only available with test API keys (fac_test_*).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def reset_data(self) -> dict[str, Any]:
        """Reset all test data and reload sandbox fixtures.

        Soft-deletes all test-mode resources (invoices, customers, products,
        quotes, credit notes, payments, recurring invoices) then reloads
        sandbox fixtures (5 customers, 10 products, 20 invoices).
        """
        resp = await self._client.post("/v1/sandbox/reset")
        return resp.json()  # type: ignore[no-any-return]

    async def simulate_status(self, invoice_id: str, status: str) -> dict[str, Any]:
        """Simulate a PA status change on a test-mode invoice.

        Useful for testing webhook handlers and status-dependent business logic
        without a real PA connection.

        Args:
            invoice_id: The invoice to update.
            status: Target status (deposited, transmitted, available, received,
                approved, refused, suspended, rejected, paid, partially_paid, overdue).
        """
        resp = await self._client.post(
            f"/v1/sandbox/simulate-status/{invoice_id}",
            json={"status": status},
        )
        return resp.json()  # type: ignore[no-any-return]

    async def create_fixtures(self) -> dict[str, Any]:
        """Alias for reset_data."""
        return await self.reset_data()
