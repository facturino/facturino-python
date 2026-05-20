"""Members resource — /v1/companies/{company_id}/members

Team member management: invite, list, update role, revoke, resend invitation.

Every method takes ``company_id`` as its first positional argument because
the API route is namespaced under the company ID. Pass the company you
want to act on each call:

    client.members.list("comp_abc")
    client.members.invite("comp_abc", email="dev@acme.com", role="editor")
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


def _base(company_id: str) -> str:
    return f"/v1/companies/{company_id}/members"


def _invite_body(params: dict[str, Any]) -> dict[str, Any]:
    """Build the invite request body.

    Accepts both snake_case and camelCase for the optional fields so
    callers can stay Pythonic locally while the HTTP payload matches
    the Zod schema (``displayName``, ``customMessage``).
    """
    body = dict(params)
    if "display_name" in body and "displayName" not in body:
        body["displayName"] = body.pop("display_name")
    if "custom_message" in body and "customMessage" not in body:
        body["customMessage"] = body.pop("custom_message")
    return body


class Members:
    """Synchronous members resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def list(self, company_id: str) -> dict[str, Any]:
        resp = self._client.get(_base(company_id))
        return resp.json()  # type: ignore[no-any-return]

    def get(self, company_id: str, member_id: str) -> dict[str, Any]:
        resp = self._client.get(f"{_base(company_id)}/{member_id}")
        return resp.json()  # type: ignore[no-any-return]

    def invite(self, company_id: str, **params: Any) -> dict[str, Any]:
        """Invite a new member to the company.

        Args:
            company_id: Target company ID (``comp_…``).
            email: Email address of the invitee.
            role: Role to assign (``"admin"``, ``"editor"`` or ``"viewer"``).
            display_name / displayName: Optional display name.
            custom_message / customMessage: Optional personal message added to the invitation email.
        """
        resp = self._client.post(_base(company_id), json=_invite_body(params))
        return resp.json()  # type: ignore[no-any-return]

    def update_role(self, company_id: str, member_id: str, role: str) -> dict[str, Any]:
        """Update a member's role.

        Args:
            role: ``"admin"``, ``"editor"`` or ``"viewer"``. Cannot promote to ``"owner"``.
        """
        resp = self._client.patch(
            f"{_base(company_id)}/{member_id}", json={"role": role}
        )
        return resp.json()  # type: ignore[no-any-return]

    def revoke(self, company_id: str, member_id: str) -> None:
        """Soft-revoke a member (sets ``status: revoked``). Cannot revoke the owner."""
        self._client.delete(f"{_base(company_id)}/{member_id}")

    def resend_invitation(self, company_id: str, member_id: str) -> dict[str, Any]:
        """Re-send the invitation email to a pending member (owner/admin only)."""
        resp = self._client.post(f"{_base(company_id)}/{member_id}/resend-invitation")
        return resp.json()  # type: ignore[no-any-return]


class AsyncMembers:
    """Asynchronous members resource."""

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def list(self, company_id: str) -> dict[str, Any]:
        resp = await self._client.get(_base(company_id))
        return resp.json()  # type: ignore[no-any-return]

    async def get(self, company_id: str, member_id: str) -> dict[str, Any]:
        resp = await self._client.get(f"{_base(company_id)}/{member_id}")
        return resp.json()  # type: ignore[no-any-return]

    async def invite(self, company_id: str, **params: Any) -> dict[str, Any]:
        """Invite a new member to the company.

        See :meth:`Members.invite` for the parameter list.
        """
        resp = await self._client.post(_base(company_id), json=_invite_body(params))
        return resp.json()  # type: ignore[no-any-return]

    async def update_role(
        self, company_id: str, member_id: str, role: str
    ) -> dict[str, Any]:
        resp = await self._client.patch(
            f"{_base(company_id)}/{member_id}", json={"role": role}
        )
        return resp.json()  # type: ignore[no-any-return]

    async def revoke(self, company_id: str, member_id: str) -> None:
        await self._client.delete(f"{_base(company_id)}/{member_id}")

    async def resend_invitation(
        self, company_id: str, member_id: str
    ) -> dict[str, Any]:
        """Re-send the invitation email to a pending member (owner/admin only)."""
        resp = await self._client.post(
            f"{_base(company_id)}/{member_id}/resend-invitation"
        )
        return resp.json()  # type: ignore[no-any-return]
