import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rss_bot.config import BotConfig, FeedConfig
from rss_bot.feed import FeedEntry
from rss_bot.main import format_entry, main
from rss_bot.telegram import TelegramError


def _make_config(tmp_path: Path, dry_run: bool = True) -> BotConfig:
    return BotConfig(
        telegram_bot_token="tok",
        telegram_channel_id="@ch",
        feeds=[FeedConfig(url="https://example.com/feed", name="Example", max_items_per_run=5)],
        state_path=tmp_path / "state.json",
        dry_run=dry_run,
    )


def _make_entry(guid: str, title: str = "Title", link: str = "https://example.com/post") -> FeedEntry:
    return FeedEntry(guid=guid, title=title, link=link, summary="Summary text", published=None)


def test_format_entry():
    entry = _make_entry("g1", title="Hello World", link="https://example.com/1")
    entry.summary = "Short summary"
    result = format_entry("My Feed", entry)
    assert "<b>My Feed</b>" in result
    assert '<a href="https://example.com/1">Hello World</a>' in result
    assert "Short summary" in result


def test_format_entry_truncates_summary():
    entry = _make_entry("g1")
    entry.summary = "x" * 300
    result = format_entry("Feed", entry)
    assert result.endswith("x" * 200)


def test_main_first_run_seeds_no_sends(tmp_path):
    config = _make_config(tmp_path)
    entries = [_make_entry("g1"), _make_entry("g2")]

    with (
        patch("rss_bot.main.load_config", return_value=config),
        patch("rss_bot.main.fetch_feed", return_value=entries),
        patch("rss_bot.main.TelegramClient") as MockClient,
    ):
        mock_client = MagicMock()
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = main()

    assert result == 0
    mock_client.send_message.assert_not_called()
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["https://example.com/feed"]["seeded"] is True
    assert set(state["https://example.com/feed"]["seen_guids"]) == {"g1", "g2"}


def test_main_second_run_sends_new_items(tmp_path):
    config = _make_config(tmp_path, dry_run=False)
    # Seed initial state
    initial_state = {
        "https://example.com/feed": {
            "seen_guids": ["g1"],
            "seeded": True,
            "last_run": "2026-01-01T00:00:00+00:00",
        }
    }
    (tmp_path / "state.json").write_text(json.dumps(initial_state))

    entries = [_make_entry("g1"), _make_entry("g2")]

    with (
        patch("rss_bot.main.load_config", return_value=config),
        patch("rss_bot.main.fetch_feed", return_value=entries),
        patch("rss_bot.main.time.sleep"),
        patch("rss_bot.main.TelegramClient") as MockClient,
    ):
        mock_client = MagicMock()
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = main()

    assert result == 0
    mock_client.send_message.assert_called_once()
    call_text = mock_client.send_message.call_args[0][0]
    assert "Title" in call_text

    state = json.loads((tmp_path / "state.json").read_text())
    assert "g2" in state["https://example.com/feed"]["seen_guids"]


def test_main_no_new_items_no_sends(tmp_path):
    config = _make_config(tmp_path, dry_run=False)
    initial_state = {
        "https://example.com/feed": {
            "seen_guids": ["g1", "g2"],
            "seeded": True,
            "last_run": "2026-01-01T00:00:00+00:00",
        }
    }
    (tmp_path / "state.json").write_text(json.dumps(initial_state))

    entries = [_make_entry("g1"), _make_entry("g2")]

    with (
        patch("rss_bot.main.load_config", return_value=config),
        patch("rss_bot.main.fetch_feed", return_value=entries),
        patch("rss_bot.main.TelegramClient") as MockClient,
    ):
        mock_client = MagicMock()
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = main()

    assert result == 0
    mock_client.send_message.assert_not_called()


def test_main_telegram_error_continues(tmp_path):
    config = _make_config(tmp_path, dry_run=False)
    initial_state = {
        "https://example.com/feed": {
            "seen_guids": [],
            "seeded": True,
            "last_run": "2026-01-01T00:00:00+00:00",
        }
    }
    (tmp_path / "state.json").write_text(json.dumps(initial_state))

    entries = [_make_entry("g1"), _make_entry("g2")]

    with (
        patch("rss_bot.main.load_config", return_value=config),
        patch("rss_bot.main.fetch_feed", return_value=entries),
        patch("rss_bot.main.time.sleep"),
        patch("rss_bot.main.TelegramClient") as MockClient,
    ):
        mock_client = MagicMock()
        mock_client.send_message.side_effect = TelegramError("rate limited")
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = main()

    # Should complete without crashing
    assert result == 0


def test_main_dry_run_skips_sends(tmp_path):
    config = _make_config(tmp_path, dry_run=True)
    initial_state = {
        "https://example.com/feed": {
            "seen_guids": [],
            "seeded": True,
            "last_run": "2026-01-01T00:00:00+00:00",
        }
    }
    (tmp_path / "state.json").write_text(json.dumps(initial_state))

    entries = [_make_entry("g1"), _make_entry("g2")]

    with (
        patch("rss_bot.main.load_config", return_value=config),
        patch("rss_bot.main.fetch_feed", return_value=entries),
        patch("rss_bot.main.TelegramClient") as MockClient,
    ):
        mock_client = MagicMock()
        MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)

        result = main()

    assert result == 0
    mock_client.send_message.assert_not_called()
    # State should still be updated
    state = json.loads((tmp_path / "state.json").read_text())
    assert "g1" in state["https://example.com/feed"]["seen_guids"]
