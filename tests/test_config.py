import os
import textwrap
from pathlib import Path

import pytest

from rss_bot.config import BotConfig, ConfigError, FeedConfig, load_config


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        feeds:
          - url: https://example.com/feed.xml
            name: Example
          - url: https://other.com/rss
            name: Other
        settings:
          max_items_per_run: 3
          state_path: data/state.json
    """)
    p = tmp_path / "config.yml"
    p.write_text(content)
    return p


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
    monkeypatch.delenv("DRY_RUN", raising=False)


def test_load_config_success(monkeypatch, config_file):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@mychannel")

    cfg = load_config(config_file)

    assert isinstance(cfg, BotConfig)
    assert cfg.telegram_bot_token == "tok123"
    assert cfg.telegram_channel_id == "@mychannel"
    assert cfg.dry_run is False
    assert cfg.state_path == Path("data/state.json")
    assert len(cfg.feeds) == 2
    assert cfg.feeds[0] == FeedConfig(url="https://example.com/feed.xml", name="Example", max_items_per_run=3)
    assert cfg.feeds[1] == FeedConfig(url="https://other.com/rss", name="Other", max_items_per_run=3)


def test_dry_run_flag(monkeypatch, config_file):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@ch")
    monkeypatch.setenv("DRY_RUN", "1")

    cfg = load_config(config_file)
    assert cfg.dry_run is True


def test_missing_token_raises(monkeypatch, config_file):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@ch")
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        load_config(config_file)


def test_missing_channel_raises(monkeypatch, config_file):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    with pytest.raises(ConfigError, match="TELEGRAM_CHANNEL_ID"):
        load_config(config_file)


def test_missing_config_file_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@ch")
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nonexistent.yml")
