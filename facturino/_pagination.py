"""Auto-pagination iterators for Facturino list endpoints.

Usage:
    # Sync iteration — automatically fetches next pages
    for invoice in client.invoices.list(limit=10):
        print(invoice["id"])

    # Async iteration
    async for invoice in async_client.invoices.list(limit=10):
        print(invoice["id"])

    # Access the first page only (no auto-pagination)
    page = client.invoices.list(limit=10)
    page.data       # list of items on this page
    page.has_more   # bool
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine, Iterator
from typing import Any


class SyncPage:
    """A single page of results from a list endpoint, with auto-pagination via iteration.

    Attributes:
        data: List of resource dicts on this page.
        has_more: Whether more items are available after this page.
        next_cursor: Cursor for the next page, if any.
        url: The API endpoint URL.
    """

    def __init__(
        self,
        data: list[dict[str, Any]],
        has_more: bool,
        next_cursor: str | None,
        url: str,
        *,
        fetcher: Callable[..., SyncPage],
        original_params: dict[str, Any],
    ) -> None:
        self.data = data
        self.has_more = has_more
        self.next_cursor = next_cursor
        self.url = url
        self._fetcher = fetcher
        self._original_params = original_params

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate through all items, automatically fetching subsequent pages."""
        page = self
        while True:
            yield from page.data
            if not page.has_more or not page.next_cursor:
                break
            params = {**page._original_params, "starting_after": page.next_cursor}
            page = page._fetcher(**params)

    def __len__(self) -> int:
        """Return the number of items on this page (not all pages)."""
        return len(self.data)

    def __repr__(self) -> str:
        return f"SyncPage(url={self.url!r}, data=[{len(self.data)} items], has_more={self.has_more})"

    @classmethod
    def from_response(
        cls,
        body: dict[str, Any],
        *,
        fetcher: Callable[..., SyncPage],
        original_params: dict[str, Any],
    ) -> SyncPage:
        return cls(
            data=body.get("data", []),
            has_more=body.get("has_more", False),
            next_cursor=body.get("next_cursor"),
            url=body.get("url", ""),
            fetcher=fetcher,
            original_params=original_params,
        )


class AsyncPage:
    """Async equivalent of SyncPage with ``async for`` support."""

    def __init__(
        self,
        data: list[dict[str, Any]],
        has_more: bool,
        next_cursor: str | None,
        url: str,
        *,
        fetcher: Callable[..., Coroutine[Any, Any, AsyncPage]],
        original_params: dict[str, Any],
    ) -> None:
        self.data = data
        self.has_more = has_more
        self.next_cursor = next_cursor
        self.url = url
        self._fetcher = fetcher
        self._original_params = original_params

    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        page = self
        while True:
            for item in page.data:
                yield item
            if not page.has_more or not page.next_cursor:
                break
            params = {**page._original_params, "starting_after": page.next_cursor}
            page = await page._fetcher(**params)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"AsyncPage(url={self.url!r}, data=[{len(self.data)} items], has_more={self.has_more})"

    @classmethod
    def from_response(
        cls,
        body: dict[str, Any],
        *,
        fetcher: Callable[..., Coroutine[Any, Any, AsyncPage]],
        original_params: dict[str, Any],
    ) -> AsyncPage:
        return cls(
            data=body.get("data", []),
            has_more=body.get("has_more", False),
            next_cursor=body.get("next_cursor"),
            url=body.get("url", ""),
            fetcher=fetcher,
            original_params=original_params,
        )
