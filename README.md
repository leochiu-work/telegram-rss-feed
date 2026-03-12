# Telegram RSS Feed Bot

A Telegram RSS Feed Bot that runs as a GitHub Actions scheduled workflow (not a long-running server). It checks RSS feeds hourly and sends new items to a Telegram channel.

## How It Works

- Triggered hourly via GitHub Actions cron schedule
- Fetches configured RSS feeds
- Sends new items to a Telegram channel
- Persists state (seen GUIDs) by committing `data/state.json` back to the repo
- On first run, seeds all current items without sending (no flood on startup)

## Setup

### 1. Fork / Clone this repo

### 2. Configure your feeds

Edit `config.yml` to add your RSS feed URLs:

```yaml
feeds:
  - url: https://example.com/feed.xml
    name: My Blog
settings:
  max_items_per_run: 5
  state_path: data/state.json
```

### 3. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token

### 4. Add GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel (`@mychannel` or `-100xxxxxxxxx`) |

### 5. Enable Actions

The workflow runs automatically every hour. You can also trigger it manually via **Actions → RSS Feed Bot → Run workflow**.

## Local Development

```bash
# Install dependencies
uv sync

# Copy and fill in your credentials
cp .env.example .env

# Dry run (no messages sent, state still saved)
DRY_RUN=1 uv run rss-bot

# Real run
uv run rss-bot
```

## Configuration

| Setting | Description |
|---------|-------------|
| `feeds[].url` | RSS feed URL |
| `feeds[].name` | Display name for the feed |
| `settings.max_items_per_run` | Max items sent per feed per run (safety cap) |
| `settings.state_path` | Path to state JSON file |

| Env Var | Description |
|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Target channel ID or username |
| `DRY_RUN` | Set to `1` to skip sending messages |

## State File

`data/state.json` tracks which items have been sent per feed:

```json
{
  "https://example.com/feed.xml": {
    "seen_guids": ["guid1", "guid2"],
    "last_run": "2026-03-12T10:00:00Z",
    "seeded": true
  }
}
```

- On **first run**: all current GUIDs are recorded but nothing is sent
- On **subsequent runs**: only new items (not in `seen_guids`) are sent
- GUIDs are capped at 500 per feed (FIFO eviction)
