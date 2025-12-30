# Telegram Music Bot (Dual Account)

This repository provides a production-ready skeleton for a dual-account Telegram music bot:

- **Bot account** for user commands and UI controls.
- **Premium account** (Telethon + PyTgCalls) for voice chat streaming.
- **Redis bridge** for real-time communication between the two processes.

## Features

- Command handling with inline playback controls
- Redis Pub/Sub bridge for state sync
- SQLite-backed queue persistence
- Audio extraction via `yt-dlp`
- Docker + docker-compose deployment
- Health check endpoint for the bridge service

## Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Fill out the values in `.env`.
3. Start services:
   ```bash
   docker-compose up --build
   ```

## Local Run

Install dependencies and run each service in its own process:

```bash
pip install -r requirements.txt
python -m telegram_music_bot.bridge_server
python -m telegram_music_bot.bot_client
python -m telegram_music_bot.premium_client
```

## Project Structure

```
telegram_music_bot/
├── bot_client.py
├── premium_client.py
├── bridge_server.py
├── queue_manager.py
├── audio_streamer.py
├── ui_components.py
└── config.py
```
