"""Configuration loading utilities."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    bot_token: str
    api_id: int
    api_hash: str
    redis_url: str
    database_path: str
    audio_cache_path: str
    bridge_channel: str
    admin_user_ids: tuple[int, ...]


    @classmethod
    def from_env(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN", "")
        api_id = int(os.getenv("API_ID", "0"))
        api_hash = os.getenv("API_HASH", "")
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        database_path = os.getenv("DATABASE_PATH", "data/music_bot.db")
        audio_cache_path = os.getenv("AUDIO_CACHE_PATH", "data/cache")
        bridge_channel = os.getenv("BRIDGE_CHANNEL", "music_bot_events")
        admin_user_ids = tuple(
            int(value)
            for value in os.getenv("ADMIN_USER_IDS", "").split(",")
            if value.strip().isdigit()
        )

        if not bot_token:
            raise ValueError("BOT_TOKEN is required")
        if api_id <= 0 or not api_hash:
            raise ValueError("API_ID and API_HASH are required")

        return cls(
            bot_token=bot_token,
            api_id=api_id,
            api_hash=api_hash,
            redis_url=redis_url,
            database_path=database_path,
            audio_cache_path=audio_cache_path,
            bridge_channel=bridge_channel,
            admin_user_ids=admin_user_ids,
        )
