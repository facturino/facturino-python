"""Reference resource — /v1/reference

Static lookup tables maintained by INSEE that integrations need to
power their own company / customer forms:

- ``legal_forms`` — French legal-form codes (SARL, SAS, EI…)
- ``naf_codes`` — French NAF activity codes (Rev. 2, 2008)

Both lists are stable and cacheable for the lifetime of the
integration's process. Callers typically fetch once on app start and
keep the result in memory.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient
from .._pagination import AsyncPage, SyncPage


class Reference:
    """Synchronous reference resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list_legal_forms(self, **params: Any) -> SyncPage:
        """List INSEE legal forms (4-digit codes + sigles + labels).

        Args:
            search: filter by label fragment to autocomplete a form field.
            limit: max items per page.
        """
        resp = self._client.get("/v1/reference/legal-forms", params=params)
        return SyncPage.from_response(
            resp.json(), fetcher=self.list_legal_forms, original_params=params
        )

    def list_naf_codes(self, **params: Any) -> SyncPage:
        """List NAF activity codes (Rev. 2).

        Args:
            search: filter on label fragments (e.g. ``"conseil"``).
            limit: max items per page.
        """
        resp = self._client.get("/v1/reference/naf-codes", params=params)
        return SyncPage.from_response(
            resp.json(), fetcher=self.list_naf_codes, original_params=params
        )


class AsyncReference:
    """Asynchronous reference resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list_legal_forms(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/reference/legal-forms", params=params)
        return AsyncPage.from_response(
            resp.json(), fetcher=self.list_legal_forms, original_params=params
        )

    async def list_naf_codes(self, **params: Any) -> AsyncPage:
        resp = await self._client.get("/v1/reference/naf-codes", params=params)
        return AsyncPage.from_response(
            resp.json(), fetcher=self.list_naf_codes, original_params=params
        )
