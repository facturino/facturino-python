"""Members resource — /v1/companies/{company_id}/members

Team member management: invite, list, update role, revoke.
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Members:
    """Synchronous members resource."""

    def __init__(self, client: SyncHttpClient, company_id: str) -> None:
        self._client = client
        self._base = f"/v1/companies/{company_id}/members"

    def list(self) -> dict[str, Any]:
        resp = self._client.get(self._base)
        return resp.json()  # type: ignore[no-any-return]

    def get(self, member_id: str) -> dict[str, Any]:
        resp = self._client.get(f"{self._base}/{member_id}")
        return resp.json()  # type: ignore[no-any-return]

    def invite(self, **params: Any) -> dict[str, Any]:
        """Invite a new member to the company.

        Args:
            email: Email address of the invitee.
            role: Role to assign ("admin", "accountant", "viewer").
            display_name / displayName: Optional display name.
        """
        body = dict(params)
        if "display_name" in body and "displayName" not in body:
            body["displayName"] = body.pop("display_name")
        resp = self._client.post(self._base, json=body)
        return resp.json()  # type: ignore[no-any-return]

    def update_role(self, member_id: str, role: str) -> dict[str, Any]:
        """Args:
            role: "admin", "accountant", or "viewer".
        """
        resp = self._client.patch(f"{self._base}/{member_id}", json={"role": role})
        return resp.json()  # type: ignore[no-any-return]

    def revoke(self, member_id: str) -> None:
        self._client.delete(f"{self._base}/{member_id}")


class AsyncMembers:
    """Asynchronous members resource.

    Team member management: invite, list, update role, revoke.
    """

    def __init__(self, client: AsyncHttpClient, company_id: str) -> None:
        self._client = client
        self._base = f"/v1/companies/{company_id}/members"

    async def list(self) -> dict[str, Any]:
        resp = await self._client.get(self._base)
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, member_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"{self._base}/{member_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def invite(self, **params: Any) -> dict[str, Any]:
        """Invite a new member to the company.

        Args:
            email: Email address of the invitee.
            role: Role to assign ("admin", "accountant", "viewer").
            display_name / displayName: Optional display name.
        """
        body = dict(params)
        if "display_name" in body and "displayName" not in body:
            body["displayName"] = body.pop("display_name")
        resp = await self._client.post(self._base, json=body)
        return resp.json()  # type: ignore[no-any-return]

    async def update_role(self, member_id: str, role: str) -> dict[str, Any]:
        """Args:
            role: "admin", "accountant", or "viewer".
        """
        resp = await self._client.patch(f"{self._base}/{member_id}", json={"role": role})
        return resp.json()  # type: ignore[no-any-return]

    async def revoke(self, member_id: str) -> None:
        await self._client.delete(f"{self._base}/{member_id}")
