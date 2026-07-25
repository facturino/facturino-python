"""Products resource — /v1/products

CRUD operations and CSV import/export for product catalog.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Products:
    """Synchronous products resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def create(self, **params: Any) -> dict[str, Any]:
        """Create a product.

        Args:
            name: Product name.
            unit_price / unitPrice: Price in integer centimes.
            vat_rate / vatRate: VAT rate in centipercent (2000 = 20.00%).
            description: Product description.
            reference: Internal reference/SKU.
            unit: Unit of measure (unit, hour, day, kg, etc.).
            tags: List of tags.
            **params: Additional fields.
        """
        body = dict(params)
        if "unit_price" in body and "unitPrice" not in body:
            body["unitPrice"] = body.pop("unit_price")
        if "vat_rate" in body and "vatRate" not in body:
            body["vatRate"] = body.pop("vat_rate")
        resp = self._client.post("/v1/products", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def list(self, **params: Any) -> SyncPage:
        """List products.

        Args:
            q: Filter by name prefix.
            category: Filter by category.
            active: Filter by active flag (bool).
            limit / starting_after: Pagination controls.
            **params: Any other supported query filter.
        """
        resp = self._client.get("/v1/products", params=params)
        return SyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    def get(self, product_id: str) -> dict[str, Any]:
        resp = self._client.get(f"/v1/products/{product_id}")
        return resp.json()  # type: ignore[no-any-return]

    def update(self, product_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "unit_price" in body and "unitPrice" not in body:
            body["unitPrice"] = body.pop("unit_price")
        if "vat_rate" in body and "vatRate" not in body:
            body["vatRate"] = body.pop("vat_rate")
        resp = self._client.patch(f"/v1/products/{product_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    def delete(self, product_id: str) -> None:
        self._client.delete(f"/v1/products/{product_id}")

    def import_csv(self, csv_string: str) -> dict[str, Any]:
        """Import products from a CSV string (max 1000 rows). Returns a job object (202 Accepted)."""
        resp = self._client.post("/v1/products/import", json={"csv": csv_string})
        return resp.json()  # type: ignore[no-any-return]

    def export_csv(self) -> str:
        """Export the product catalog as raw CSV (Content-Type text/csv)."""
        resp = self._client.get("/v1/products/export")
        return resp.text


class AsyncProducts:
    """Asynchronous products resource.

    CRUD operations and CSV import/export for product catalog.
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def create(self, **params: Any) -> dict[str, Any]:
        """Create a product.

        Args:
            name: Product name.
            unit_price / unitPrice: Price in integer centimes.
            vat_rate / vatRate: VAT rate in centipercent (2000 = 20.00%).
            description: Product description.
            reference: Internal reference/SKU.
            unit: Unit of measure (unit, hour, day, kg, etc.).
            tags: List of tags.
            **params: Additional fields.
        """
        body = dict(params)
        if "unit_price" in body and "unitPrice" not in body:
            body["unitPrice"] = body.pop("unit_price")
        if "vat_rate" in body and "vatRate" not in body:
            body["vatRate"] = body.pop("vat_rate")
        resp = await self._client.post("/v1/products", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def list(self, **params: Any) -> AsyncPage:
        """List products.

        Args:
            q: Filter by name prefix.
            category: Filter by category.
            active: Filter by active flag (bool).
            limit / starting_after: Pagination controls.
            **params: Any other supported query filter.
        """
        resp = await self._client.get("/v1/products", params=params)
        return AsyncPage.from_response(resp.json(), fetcher=self.list, original_params=params)

    async def get(self, product_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"/v1/products/{product_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def update(self, product_id: str, **params: Any) -> dict[str, Any]:
        body = dict(params)
        if "unit_price" in body and "unitPrice" not in body:
            body["unitPrice"] = body.pop("unit_price")
        if "vat_rate" in body and "vatRate" not in body:
            body["vatRate"] = body.pop("vat_rate")
        resp = await self._client.patch(f"/v1/products/{product_id}", json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def delete(self, product_id: str) -> None:
        await self._client.delete(f"/v1/products/{product_id}")

    async def import_csv(self, csv_string: str) -> dict[str, Any]:
        """Import products from a CSV string (max 1000 rows). Returns a job object (202 Accepted)."""
        resp = await self._client.post("/v1/products/import", json={"csv": csv_string})
        return resp.json()  # type: ignore[no-any-return]

    async def export_csv(self) -> str:
        """Export the product catalog as raw CSV (Content-Type text/csv)."""
        resp = await self._client.get("/v1/products/export")
        return resp.text
