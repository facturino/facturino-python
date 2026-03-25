"""MFA resource — /v1/auth/mfa

Setup, verify, disable TOTP-based multi-factor authentication,
and generate backup codes (Pro plan).
"""

from __future__ import annotations

from typing import Any

from .._client import AsyncHttpClient, SyncHttpClient


class Mfa:
    """Synchronous MFA resource."""

    def __init__(self, client: SyncHttpClient) -> None:
        self._client = client

    def setup(self) -> dict[str, Any]:
        """Initialize TOTP setup.

        Returns:
            Dict with ``object``, ``secret`` (base32), and ``uri`` (otpauth:// URI).
        """
        resp = self._client.post("/v1/auth/mfa/setup")
        return resp.json()  # type: ignore[no-any-return]

    def verify(self, *, code: str) -> dict[str, Any]:
        """Verify a TOTP code and enable MFA.

        Args:
            code: 6-digit TOTP code from authenticator app.

        Returns:
            Dict with ``object`` and ``enabled: true``.
        """
        resp = self._client.post("/v1/auth/mfa/verify", json={"code": code})
        return resp.json()  # type: ignore[no-any-return]

    def disable(self, *, code: str) -> dict[str, Any]:
        """Disable MFA (requires a valid TOTP code).

        Args:
            code: 6-digit TOTP code to confirm identity.

        Returns:
            Dict with ``object`` and ``deleted: true``.
        """
        resp = self._client.delete("/v1/auth/mfa", json={"code": code})
        return resp.json()  # type: ignore[no-any-return]

    def backup_codes(self) -> dict[str, Any]:
        """Generate backup codes (MFA must be enabled first).

        Returns:
            Dict with ``object`` and ``codes`` (list of backup code strings).
        """
        resp = self._client.post("/v1/auth/mfa/backup-codes")
        return resp.json()  # type: ignore[no-any-return]


class AsyncMfa:
    """Asynchronous MFA resource.

    Setup, verify, disable TOTP-based multi-factor authentication,
    and generate backup codes (Pro plan).
    """

    def __init__(self, client: AsyncHttpClient) -> None:
        self._client = client

    async def setup(self) -> dict[str, Any]:
        """Initialize TOTP setup.

        Returns:
            Dict with ``object``, ``secret`` (base32), and ``uri`` (otpauth:// URI).
        """
        resp = await self._client.post("/v1/auth/mfa/setup")
        return resp.json()  # type: ignore[no-any-return]

    async def verify(self, *, code: str) -> dict[str, Any]:
        """Verify a TOTP code and enable MFA.

        Args:
            code: 6-digit TOTP code from authenticator app.

        Returns:
            Dict with ``object`` and ``enabled: true``.
        """
        resp = await self._client.post("/v1/auth/mfa/verify", json={"code": code})
        return resp.json()  # type: ignore[no-any-return]

    async def disable(self, *, code: str) -> dict[str, Any]:
        """Disable MFA (requires a valid TOTP code).

        Args:
            code: 6-digit TOTP code to confirm identity.

        Returns:
            Dict with ``object`` and ``deleted: true``.
        """
        resp = await self._client.delete("/v1/auth/mfa", json={"code": code})
        return resp.json()  # type: ignore[no-any-return]

    async def backup_codes(self) -> dict[str, Any]:
        """Generate backup codes (MFA must be enabled first).

        Returns:
            Dict with ``object`` and ``codes`` (list of backup code strings).
        """
        resp = await self._client.post("/v1/auth/mfa/backup-codes")
        return resp.json()  # type: ignore[no-any-return]
