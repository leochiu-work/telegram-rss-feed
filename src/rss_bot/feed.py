from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser


@dataclass
class FeedEntry:
    guid: str
    title: str
    link: str
    summary: str
    published: datetime | None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _derive_guid(entry) -> str:
    if getattr(entry, "id", None):
        return entry.id
    key = (getattr(entry, "link", "") or "") + (getattr(entry, "title", "") or "")
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _parse_published(entry) -> datetime | None:
    published_parsed = getattr(entry, "published_parsed", None)
    if published_parsed:
        try:
            import time as _time
            return datetime.fromtimestamp(_time.mktime(published_parsed))
        except Exception:
            pass
    published_str = getattr(entry, "published", None)
    if published_str:
        try:
            return parsedate_to_datetime(published_str)
        except Exception:
            pass
    return None


def fetch_feed(url: str) -> list[FeedEntry]:
    try:
        parsed = feedparser.parse(url)
        entries = []
        for entry in parsed.entries:
            guid = _derive_guid(entry)
            title = getattr(entry, "title", "") or ""
            link = getattr(entry, "link", "") or ""
            raw_summary = getattr(entry, "summary", "") or ""
            summary = _strip_html(raw_summary)
            published = _parse_published(entry)
            entries.append(FeedEntry(guid=guid, title=title, link=link, summary=summary, published=published))
        return entries
    except Exception:
        return []
