from __future__ import annotations

import httpx


class TelegramError(Exception):
    pass


class TelegramClient:
    _BASE_URL = "https://api.telegram.org"

    def __init__(self, token: str, channel_id: str) -> None:
        self._token = token
        self._channel_id = channel_id
        self._client = httpx.Client(base_url=self._BASE_URL, timeout=30)

    def send_message(self, text: str) -> None:
        url = f"/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._channel_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise TelegramError(f"Telegram API error: {data.get('description', 'unknown')}")
        except httpx.HTTPStatusError as exc:
            raise TelegramError(f"HTTP error {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise TelegramError(f"Request failed: {exc}") from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TelegramClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
