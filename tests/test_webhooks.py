"""Tests for webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

import facturino
from facturino._errors import SignatureVerificationError
from facturino._webhooks import Webhook

SECRET = "whsec_test_secret_key_for_testing"


def _make_signature(payload: str, secret: str, timestamp: int) -> str:
    """Compute a valid Facturino-Signature header."""
    signed_payload = f"{timestamp}.{payload}"
    sig = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


class TestWebhookVerification:
    def test_valid_signature(self):
        payload = json.dumps({
            "id": "evt_test_123",
            "type": "invoice.created",
            "data": {"id": "inv_abc"},
        })
        timestamp = int(time.time())
        signature = _make_signature(payload, SECRET, timestamp)

        event = Webhook.construct_event(payload, signature, SECRET)

        assert event["id"] == "evt_test_123"
        assert event["type"] == "invoice.created"

    def test_valid_signature_bytes_payload(self):
        payload = json.dumps({"id": "evt_bytes", "type": "invoice.finalized"})
        timestamp = int(time.time())
        signature = _make_signature(payload, SECRET, timestamp)

        event = Webhook.construct_event(payload.encode("utf-8"), signature, SECRET)

        assert event["id"] == "evt_bytes"

    def test_invalid_signature_raises(self):
        payload = json.dumps({"id": "evt_1"})
        timestamp = int(time.time())
        bad_sig = f"t={timestamp},v1=invalid_hex_signature"

        with pytest.raises(SignatureVerificationError, match="Signature mismatch"):
            Webhook.construct_event(payload, bad_sig, SECRET)

    def test_missing_timestamp_raises(self):
        payload = json.dumps({"id": "evt_1"})
        sig = "v1=abc123"

        with pytest.raises(SignatureVerificationError, match="Missing timestamp"):
            Webhook.construct_event(payload, sig, SECRET)

    def test_missing_v1_raises(self):
        payload = json.dumps({"id": "evt_1"})
        sig = f"t={int(time.time())}"

        with pytest.raises(SignatureVerificationError, match="Missing v1 signature"):
            Webhook.construct_event(payload, sig, SECRET)

    def test_invalid_timestamp_raises(self):
        payload = json.dumps({"id": "evt_1"})
        sig = "t=not_a_number,v1=abc123"

        with pytest.raises(SignatureVerificationError, match="Invalid timestamp"):
            Webhook.construct_event(payload, sig, SECRET)

    def test_expired_timestamp_raises(self):
        payload = json.dumps({"id": "evt_1"})
        old_timestamp = int(time.time()) - 600  # 10 minutes ago
        signature = _make_signature(payload, SECRET, old_timestamp)

        with pytest.raises(SignatureVerificationError, match="too old"):
            Webhook.construct_event(payload, signature, SECRET, tolerance=300)

    def test_custom_tolerance(self):
        payload = json.dumps({"id": "evt_1"})
        # 8 minutes ago
        timestamp = int(time.time()) - 480
        signature = _make_signature(payload, SECRET, timestamp)

        # Default 300s tolerance should reject
        with pytest.raises(SignatureVerificationError, match="too old"):
            Webhook.construct_event(payload, signature, SECRET, tolerance=300)

        # 600s tolerance should accept
        event = Webhook.construct_event(payload, signature, SECRET, tolerance=600)
        assert event["id"] == "evt_1"

    def test_tampered_payload_raises(self):
        original = json.dumps({"id": "evt_1", "amount": 10000})
        timestamp = int(time.time())
        signature = _make_signature(original, SECRET, timestamp)

        tampered = json.dumps({"id": "evt_1", "amount": 99999})

        with pytest.raises(SignatureVerificationError, match="Signature mismatch"):
            Webhook.construct_event(tampered, signature, SECRET)

    def test_wrong_secret_raises(self):
        payload = json.dumps({"id": "evt_1"})
        timestamp = int(time.time())
        signature = _make_signature(payload, SECRET, timestamp)

        with pytest.raises(SignatureVerificationError, match="Signature mismatch"):
            Webhook.construct_event(payload, signature, "wrong_secret")

    def test_verify_header_standalone(self):
        payload = json.dumps({"id": "evt_1"})
        timestamp = int(time.time())
        signature = _make_signature(payload, SECRET, timestamp)

        # Should not raise
        Webhook.verify_header(payload, signature, SECRET)

    def test_signature_with_extra_whitespace(self):
        payload = json.dumps({"id": "evt_ws"})
        timestamp = int(time.time())
        sig = _make_signature(payload, SECRET, timestamp)
        # Add spaces around parts
        parts = sig.split(",")
        sig_with_spaces = f" {parts[0]} , {parts[1]} "

        event = Webhook.construct_event(payload, sig_with_spaces, SECRET)
        assert event["id"] == "evt_ws"


class TestWebhookImport:
    def test_webhook_accessible_from_package(self):
        assert facturino.Webhook is Webhook

    def test_signature_error_accessible(self):
        assert facturino.SignatureVerificationError is SignatureVerificationError
