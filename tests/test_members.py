"""Tests for the ``members`` resource — invite, list, role updates."""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino


@respx.mock
def test_members_invite_maps_snake_case_to_camel() -> None:
    """Pythonic ``display_name`` / ``custom_message`` must be re-keyed to
    camelCase before hitting the API.
    """
    route = respx.post(
        "https://facturino.com/api/v1/companies/comp_abc/members"
    ).mock(return_value=httpx.Response(201, json={"id": "mem_1", "status": "pending"}))

    client = facturino.Client("fac_test_abc123")
    client.members.invite(
        "comp_abc",
        email="dev@acme.com",
        role="editor",
        display_name="Dev Acme",
        custom_message="Welcome aboard!",
    )

    assert route.called
    body = route.calls[0].request.read()
    # API expects camelCase — snake_case keys MUST NOT leak through.
    assert b"displayName" in body
    assert b"customMessage" in body
    assert b"display_name" not in body
    assert b"custom_message" not in body


@respx.mock
def test_members_list_takes_company_id() -> None:
    route = respx.get(
        "https://facturino.com/api/v1/companies/comp_abc/members"
    ).mock(return_value=httpx.Response(200, json={"object": "list", "data": []}))

    client = facturino.Client("fac_test_abc123")
    client.members.list("comp_abc")
    assert route.called


@respx.mock
def test_members_resend_invitation() -> None:
    route = respx.post(
        "https://facturino.com/api/v1/companies/comp_abc/members/mem_1/resend-invitation"
    ).mock(return_value=httpx.Response(200, json={"id": "mem_1", "status": "pending"}))

    client = facturino.Client("fac_test_abc123")
    client.members.resend_invitation("comp_abc", "mem_1")
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_async_members_invite() -> None:
    route = respx.post(
        "https://facturino.com/api/v1/companies/comp_abc/members"
    ).mock(return_value=httpx.Response(201, json={"id": "mem_2"}))

    async with facturino.AsyncClient("fac_test_abc123") as client:
        await client.members.invite("comp_abc", email="ops@acme.com", role="viewer")

    assert route.called
