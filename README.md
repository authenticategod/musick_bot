# Telegram Dual-Account Music Bot

This repository contains a scaffold for a dual-account Telegram music bot that uses:

- **Bot account** (Bot API) for commands and UI
- **Premium user account** (MTProto) for joining voice chats and streaming audio
- **Bridge server** for inter-process communication

## Quick start

1. Create a `.env` file with your credentials (see `.env.example`).
2. Start the stack:

```bash
docker compose up --build
```

## Configuration

Environment variables are loaded from the process environment and never stored in the repo.

| Variable | Description |
| --- | --- |
| `BOT_TOKEN` | Telegram bot token |
| `API_ID` | Telegram app API ID |
| `API_HASH` | Telegram app API hash |
| `SESSION_NAME` | Telethon session name |
| `REDIS_URL` | Redis connection URL |
| `DATABASE_URL` | SQLite database file path |
| `SPOTIFY_CLIENT_ID` | Spotify application client id (optional) |
| `SPOTIFY_CLIENT_SECRET` | Spotify application client secret (optional) |
| `BRIDGE_PORT` | Bridge WebSocket port |
| `HEALTH_PORT` | Bridge health check port |
| `LOG_LEVEL` | Logging level |

## Security

Never commit real tokens or secrets to version control. If a token is ever shared publicly, **rotate it immediately**.
