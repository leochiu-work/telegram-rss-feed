import httpx
import pytest
from pytest_httpx import HTTPXMock

from rss_bot.telegram import TelegramClient, TelegramError


TOKEN = "bot123:testtoken"
CHANNEL = "@testchannel"
BASE = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


@pytest.fixture
def client():
    with TelegramClient(TOKEN, CHANNEL) as c:
        yield c


def test_send_message_success(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=BASE,
        json={"ok": True, "result": {"message_id": 1}},
    )
    client.send_message("Hello!")  # should not raise


def test_send_message_telegram_not_ok(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=BASE,
        json={"ok": False, "description": "Bad Request"},
    )
    with pytest.raises(TelegramError, match="Bad Request"):
        client.send_message("Hello!")


def test_send_message_http_error(client, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=BASE, status_code=500, text="Internal Server Error")
    with pytest.raises(TelegramError, match="HTTP error 500"):
        client.send_message("Hello!")


def test_send_message_network_error(client, httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))
    with pytest.raises(TelegramError, match="Request failed"):
        client.send_message("Hello!")


def test_context_manager_closes_client(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=BASE, json={"ok": True, "result": {}})
    with TelegramClient(TOKEN, CHANNEL) as c:
        c.send_message("test")
    # No exception = client closed cleanly
