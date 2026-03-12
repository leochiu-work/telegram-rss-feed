from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


class ConfigError(Exception):
    pass


@dataclass
class FeedConfig:
    url: str
    name: str
    max_items_per_run: int = 5


@dataclass
class BotConfig:
    telegram_bot_token: str
    telegram_channel_id: str
    feeds: list[FeedConfig]
    state_path: Path
    dry_run: bool = False


def load_config(config_path: str | Path = "config.yml") -> BotConfig:
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    dry_run = os.environ.get("DRY_RUN", "0").strip() == "1"

    if not token:
        raise ConfigError("TELEGRAM_BOT_TOKEN environment variable is not set")
    if not channel_id:
        raise ConfigError("TELEGRAM_CHANNEL_ID environment variable is not set")

    config_path = Path(config_path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open() as f:
        raw = yaml.safe_load(f)

    settings = raw.get("settings", {})
    max_items = settings.get("max_items_per_run", 5)
    state_path = Path(settings.get("state_path", "data/state.json"))

    feeds = [
        FeedConfig(
            url=feed["url"],
            name=feed["name"],
            max_items_per_run=max_items,
        )
        for feed in raw.get("feeds", [])
    ]

    return BotConfig(
        telegram_bot_token=token,
        telegram_channel_id=channel_id,
        feeds=feeds,
        state_path=state_path,
        dry_run=dry_run,
    )
