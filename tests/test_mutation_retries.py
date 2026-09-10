import json
import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from facturino._client import SyncHttpClient, AsyncHttpClient, _get_retry_delay
from facturino._errors import ApiError, FacturinoError

KEY = "fac_test_local"
ERROR = {"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded", "message": "Slow down"}}

@contextmanager
def cut_response_server():
    state = {"keys": [], "movements": {}}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            key = self.headers.get("Idempotency-Key", "")
            state["keys"].append(key)
            state["movements"].setdefault(key, len(state["movements"]) + 1)
            if len(state["keys"]) == 1:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            body = json.dumps({"id": state["movements"][key]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_real_server_applies_once_after_response_loss():
    with cut_response_server() as (url, state), SyncHttpClient(KEY, base_url=url) as client:
        assert client.post("/payments", json={"amount": 1188}).json() == {"id": 1}
        assert len(state["movements"]) == 1
        assert len(state["keys"]) == 2
        assert state["keys"][0] and state["keys"][0] == state["keys"][1]
        assert client.post("/payments", json={"amount": 1188}).json() == {"id": 2}


async def test_async_real_server_applies_once_after_response_loss():
    with cut_response_server() as (url, state):
        async with AsyncHttpClient(KEY, base_url=url) as client:
            assert (await client.post("/payments", json={"amount": 1188})).json() == {"id": 1}
            assert len(state["movements"]) == 1
            assert len(state["keys"]) == 2
            assert state["keys"][0] and state["keys"][0] == state["keys"][1]


@respx.mock
def test_retry_after_long_wait_is_exact():
    route = respx.post("https://facturino.com/api/payments").mock(side_effect=[
        httpx.Response(429, json=ERROR, headers={"Retry-After": "90"}), httpx.Response(200, json={}),
    ])
    with SyncHttpClient(KEY, retry_budget=100) as client, patch("facturino._client.time.sleep") as sleep:
        assert client.post("/payments", json={}).status_code == 200
        sleep.assert_called_once_with(90.0)
        assert route.call_count == 2


@respx.mock
async def test_async_retry_after_long_wait_is_exact():
    respx.post("https://facturino.com/api/payments").mock(side_effect=[
        httpx.Response(429, json=ERROR, headers={"Retry-After": "90"}), httpx.Response(200, json={}),
    ])
    async with AsyncHttpClient(KEY, retry_budget=100) as client:
        with patch("facturino._client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            await client.post("/payments", json={})
            sleep.assert_awaited_once_with(90.0)


@pytest.mark.parametrize("async_client", [False, True])
@respx.mock
async def test_retry_after_budget_returns_original_429(async_client):
    route = respx.post("https://facturino.com/api/payments").mock(return_value=httpx.Response(429, json=ERROR, headers={"Retry-After": "90"}))
    with patch("facturino._client.time.sleep") as sync_sleep, patch("facturino._client.asyncio.sleep", new_callable=AsyncMock) as async_sleep:
        with pytest.raises(ApiError) as error:
            if async_client:
                async with AsyncHttpClient(KEY) as client:
                    await client.post("/payments", json={})
            else:
                with SyncHttpClient(KEY) as client:
                    client.post("/payments", json={})
        assert error.value.status_code == 429
        assert route.call_count == 1
        sync_sleep.assert_not_called()
        async_sleep.assert_not_awaited()


@pytest.mark.parametrize("async_client", [False, True])
@respx.mock
async def test_unkeyed_posts_never_retry(async_client):
    route = respx.post("https://facturino.com/api/payments").mock(side_effect=httpx.RemoteProtocolError("response cut"))
    with pytest.raises(FacturinoError):
        if async_client:
            async with AsyncHttpClient(KEY, auto_idempotency=False) as client:
                await client.post("/payments", json={})
        else:
            with SyncHttpClient(KEY, auto_idempotency=False) as client:
                client.post("/payments", json={})
    assert route.call_count == 1
    assert "idempotency-key" not in route.calls[0].request.headers


@respx.mock
def test_header_key_is_preserved_with_generation_disabled():
    route = respx.post("https://facturino.com/api/payments").mock(side_effect=[httpx.Response(429, json=ERROR, headers={"Retry-After": "0"}), httpx.Response(200, json={})])
    with SyncHttpClient(KEY, auto_idempotency=False) as client:
        client.post("/payments", json={}, headers={"Idempotency-Key": "caller-key"})
    assert [call.request.headers["idempotency-key"] for call in route.calls] == ["caller-key", "caller-key"]


def test_retry_after_date_and_invalid_values():
    with patch("facturino._client.time.time", return_value=0):
        assert _get_retry_delay(0, httpx.Response(429, headers={"Retry-After": "Thu, 01 Jan 1970 00:01:30 GMT"})) == 90
    assert _get_retry_delay(0, httpx.Response(429, headers={"Retry-After": "NaN"})) == 0.5
