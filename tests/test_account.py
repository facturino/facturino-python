"""Tests for the ``account`` resource — synchronous and asynchronous."""

from __future__ import annotations

import httpx
import pytest
import respx

import facturino


@respx.mock
def test_account_retrieve_hits_v1_account() -> None:
    """``account.retrieve()`` must GET /v1/account and return the JSON body."""
    payload = {
        "object": "account",
        "userId": "usr_abc",
        "companyId": "comp_xyz",
        "plan": "pro",
        "livemode": False,
        "apiKeyPrefix": "fac_test_",
        "permissions": [],
        "company": {"id": "comp_xyz", "name": "ACME"},
        "user": {"emailVerified": True},
    }
    route = respx.get("https://facturino.com/api/v1/account").mock(
        return_value=httpx.Response(200, json=payload)
    )

    client = facturino.Client("fac_test_abc123")
    result = client.account.retrieve()

    assert route.called
    assert result == payload
    assert result["livemode"] is False
    assert result["apiKeyPrefix"] == "fac_test_"


@respx.mock
def test_account_retrieve_handles_unconnected_company() -> None:
    """The endpoint can return ``company: None`` for users without a company."""
    respx.get("https://facturino.com/api/v1/account").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "account",
                "userId": "usr_live",
                "companyId": "",
                "plan": "free",
                "livemode": True,
                "apiKeyPrefix": "fac_live_",
                "permissions": [],
                "company": None,
                "user": {"emailVerified": False},
            },
        )
    )

    client = facturino.Client("fac_live_abc123")
    result = client.account.retrieve()
    assert result["company"] is None
    assert result["livemode"] is True


@respx.mock
@pytest.mark.asyncio
async def test_async_account_retrieve() -> None:
    payload = {
        "object": "account",
        "userId": "usr_async",
        "companyId": "comp_async",
        "plan": "essential",
        "livemode": False,
        "apiKeyPrefix": "fac_test_",
        "permissions": [],
        "company": {"id": "comp_async"},
        "user": {"emailVerified": False},
    }
    respx.get("https://facturino.com/api/v1/account").mock(
        return_value=httpx.Response(200, json=payload)
    )

    async with facturino.AsyncClient("fac_test_abc123") as client:
        result = await client.account.retrieve()

    assert result == payload
