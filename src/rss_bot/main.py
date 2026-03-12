from __future__ import annotations

import sys
import time

from rss_bot.config import load_config
from rss_bot.feed import FeedEntry, fetch_feed
from rss_bot.state import is_seeded, load_state, mark_seen, save_state, seen_guids
from rss_bot.telegram import TelegramClient, TelegramError


def format_entry(feed_name: str, entry: FeedEntry) -> str:
    summary = entry.summary[:200] if entry.summary else ""
    return f"<b>{feed_name}</b>\n<a href=\"{entry.link}\">{entry.title}</a>\n\n{summary}"


def main() -> int:
    config = load_config()
    state = load_state(config.state_path)

    with TelegramClient(config.telegram_bot_token, config.telegram_channel_id) as client:
        for feed in config.feeds:
            print(f"Checking feed: {feed.name} ({feed.url})")
            entries = fetch_feed(feed.url)

            if not is_seeded(state, feed.url):
                print(f"  First run — seeding {len(entries)} entries, no messages sent.")
                mark_seen(state, feed.url, [e.guid for e in entries], seeded=True)
                continue

            already_seen = seen_guids(state, feed.url)
            new_entries = [e for e in entries if e.guid not in already_seen]
            to_send = list(reversed(new_entries[: feed.max_items_per_run]))  # oldest-first

            if not to_send:
                print(f"  No new items.")
                continue

            print(f"  {len(to_send)} new item(s) to send.")
            for entry in to_send:
                if not config.dry_run:
                    try:
                        client.send_message(format_entry(feed.name, entry))
                        time.sleep(0.5)
                    except TelegramError as exc:
                        print(f"  ERROR sending '{entry.title}': {exc}", file=sys.stderr)
                        continue
                else:
                    print(f"  [DRY RUN] Would send: {entry.title}")
                mark_seen(state, feed.url, [entry.guid])

    save_state(config.state_path, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
