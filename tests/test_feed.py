from unittest.mock import MagicMock, patch

import pytest

from rss_bot.feed import FeedEntry, fetch_feed, _strip_html, _derive_guid


def _make_entry(id=None, title="Title", link="https://example.com/post", summary="<p>Hello</p>", published_parsed=None):
    entry = MagicMock()
    entry.id = id
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.published_parsed = published_parsed
    entry.published = None
    return entry


def test_strip_html_removes_tags():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_strip_html_plain_text_unchanged():
    assert _strip_html("plain text") == "plain text"


def test_derive_guid_uses_id_when_present():
    entry = _make_entry(id="unique-id-123")
    assert _derive_guid(entry) == "unique-id-123"


def test_derive_guid_falls_back_to_hash():
    entry = _make_entry(id=None, link="https://example.com", title="Hello")
    guid = _derive_guid(entry)
    assert len(guid) == 16
    # deterministic
    assert _derive_guid(entry) == guid


def test_fetch_feed_returns_entries():
    mock_parsed = MagicMock()
    entry = _make_entry(id="g1", title="Test Post", link="https://example.com/1", summary="<b>Content</b>")
    mock_parsed.entries = [entry]

    with patch("rss_bot.feed.feedparser.parse", return_value=mock_parsed):
        result = fetch_feed("https://example.com/feed.xml")

    assert len(result) == 1
    assert result[0].guid == "g1"
    assert result[0].title == "Test Post"
    assert result[0].link == "https://example.com/1"
    assert result[0].summary == "Content"


def test_fetch_feed_returns_empty_on_error():
    with patch("rss_bot.feed.feedparser.parse", side_effect=Exception("network error")):
        result = fetch_feed("https://bad.url/feed")
    assert result == []


def test_fetch_feed_empty_feed():
    mock_parsed = MagicMock()
    mock_parsed.entries = []
    with patch("rss_bot.feed.feedparser.parse", return_value=mock_parsed):
        result = fetch_feed("https://example.com/empty.xml")
    assert result == []


def test_fetch_feed_strips_html_summary():
    mock_parsed = MagicMock()
    entry = _make_entry(summary="<p>Hello <a href='#'>world</a></p>")
    mock_parsed.entries = [entry]
    with patch("rss_bot.feed.feedparser.parse", return_value=mock_parsed):
        result = fetch_feed("https://example.com/feed")
    assert result[0].summary == "Hello world"
