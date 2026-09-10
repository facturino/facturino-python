"""Webhook signature verification for Facturino webhooks.

The Facturino API signs webhook payloads using HMAC-SHA256. The signature
is sent in the ``Facturino-Signature`` header with the format:

    t=<unix_timestamp>,v1=<hex_hmac>

Verification:
    1. Extract ``t`` (timestamp) and ``v1`` (signature) from the header.
    2. Rebuild the signed payload: ``{t}.{raw_body}``.
    3. Compute HMAC-SHA256 of the signed payload using the endpoint secret.
    4. Compare in constant time.
    5. Reject if the timestamp is too old (anti-replay, default 5 minutes).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from ._errors import SignatureVerificationError
from ._types import WebhookEvent

# Default tolerance: 5 minutes (300 seconds)
DEFAULT_TOLERANCE = 300


class Webhook:
    """Utility class for verifying Facturino webhook signatures."""

    @staticmethod
    def construct_event(
        payload: str | bytes,
        signature: str,
        secret: str,
        *,
        tolerance: int = DEFAULT_TOLERANCE,
    ) -> WebhookEvent:
        """Verify a webhook signature and return the parsed event.

        Args:
            payload: Raw request body (str or bytes). Must be the exact bytes
                received — do not parse or re-serialize before verifying.
            signature: Value of the ``Facturino-Signature`` header.
            secret: The webhook endpoint secret (``whsec_...``).
            tolerance: Maximum age in seconds for the event timestamp.
                Defaults to 300 (5 minutes).

        Returns:
            Parsed event dict.

        Raises:
            SignatureVerificationError: If the signature is invalid, the
                timestamp is missing, or the event is too old.
        """
        Webhook.verify_header(payload, signature, secret, tolerance=tolerance)

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        return json.loads(payload)  # type: ignore[no-any-return]

    @staticmethod
    def verify_header(
        payload: str | bytes,
        signature: str,
        secret: str,
        *,
        tolerance: int = DEFAULT_TOLERANCE,
    ) -> None:
        """Verify a webhook signature header.

        Raises:
            SignatureVerificationError: On any verification failure.
        """
        if isinstance(payload, bytes):
            payload_str = payload.decode("utf-8")
        else:
            payload_str = payload

        # Parse header: t=<timestamp>,v1=<hex>
        timestamp: int | None = None
        received_sig: str | None = None

        for part in signature.split(","):
            part = part.strip()
            if part.startswith("t="):
                try:
                    timestamp = int(part[2:])
                except ValueError:
                    raise SignatureVerificationError(
                        "Invalid timestamp in Facturino-Signature header"
                    )
            elif part.startswith("v1="):
                received_sig = part[3:]

        if timestamp is None:
            raise SignatureVerificationError(
                "Missing timestamp in Facturino-Signature header"
            )

        if received_sig is None:
            raise SignatureVerificationError(
                "Missing v1 signature in Facturino-Signature header"
            )

        # Anti-replay check
        now = int(time.time())
        if abs(now - timestamp) > tolerance:
            raise SignatureVerificationError(
                f"Webhook timestamp too old (received {timestamp}, "
                f"current {now}, tolerance {tolerance}s)"
            )

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload_str}"
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Timing-safe comparison
        if not hmac.compare_digest(expected_sig, received_sig):
            raise SignatureVerificationError(
                "Signature mismatch — the payload may have been tampered with"
            )
