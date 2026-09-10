import json
from pathlib import Path

import httpx
import respx

import facturino


@respx.mock
def test_registry_disclosure_is_preserved_without_identity_fallback():
    body = json.loads((Path(__file__).parent / "fixtures/contract/registry-disclosure.json").read_text())
    respx.post("https://facturino.com/api/v1/customers/lookup").mock(return_value=httpx.Response(200, json=body))
    actual = facturino.Client("fac_test_fixture").customers.lookup(siret=body["data"]["siret"])
    assert actual == body
    assert actual["data"]["name"] == ""
    assert actual["data"]["disclosure"]["status"] == "P"
