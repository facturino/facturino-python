import json
from pathlib import Path
from typing import get_type_hints

from facturino._types import InvoiceEinvoicing, InvoiceSubmissionArtefact, PaymentCollectionStatus, WebhookEventData
from facturino.event_data import PaymentReceivedWebhookData


def test_after_train_typed_fields_and_nullable_event_attribution():
    corpus = json.loads((Path(__file__).parent / "fixtures/contract/after-train.json").read_text())
    assert "senderRoutingIdentifier" in get_type_hints(InvoiceEinvoicing)
    assert "sellerRoutingIdentifier" in get_type_hints(InvoiceSubmissionArtefact)
    for model in (PaymentReceivedWebhookData, WebhookEventData):
        fields = get_type_hints(model)
        assert fields["paymentId"] == str | None
        assert fields["fr212"] == PaymentCollectionStatus | None
    assert corpus["paymentEvent"]["data"]["paymentId"] == "pay_example"
    assert corpus["paymentEvent"]["data"]["fr212"]["state"] == "pending"
    assert "paymentId" not in corpus["legacyPaymentEvent"]["data"]
    assert corpus["unattributedPaymentEvent"]["data"]["paymentId"] is None
