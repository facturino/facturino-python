import json
from pathlib import Path
from typing import get_type_hints

from facturino._types import (
    CreditNoteEinvoicing,
    EReporting,
    InvoiceEinvoicing,
    ObligationFollowUp,
    Payment,
    PaymentCollectionStatus,
    WebhookEventData,
)
from facturino.event_data import EVENT_DATA_TYPES, ObligationWebhookData


def test_autonomous_obligation_contract():
    corpus = json.loads((Path(__file__).parent / "fixtures/contract/autonomy.json").read_text())
    for model in (InvoiceEinvoicing, CreditNoteEinvoicing, PaymentCollectionStatus, EReporting, WebhookEventData):
        assert get_type_hints(model)["obligation"] == ObligationFollowUp | None
    assert get_type_hints(Payment)["reportingFollowUp"] == ObligationFollowUp | None
    for event in corpus["events"]:
        assert EVENT_DATA_TYPES[event["type"]] == ObligationWebhookData
        assert event["data"]["obligation"]["owner"] == "facturino"
    assert corpus["completed"]["owner"] is None
    assert corpus["customerAction"]["owner"] == "customer" and corpus["customerAction"]["action"] == "connect_platform"
    assert "obligation" not in corpus["legacy"]
