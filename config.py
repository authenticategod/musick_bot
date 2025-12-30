import os
from dataclasses import dataclass


def _env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


@dataclass(frozen=True)
class BotConfig:
    bot_token: str
    redis_url: str
    database_url: str
    log_level: str
    spotify_client_id: str | None
    spotify_client_secret: str | None


@dataclass(frozen=True)
class PremiumConfig:
    api_id: int
    api_hash: str
    session_name: str
    redis_url: str
    log_level: str


@dataclass(frozen=True)
class BridgeConfig:
    redis_url: str
    host: str
    port: int
    health_port: int
    log_level: str



def load_bot_config() -> BotConfig:
    return BotConfig(
        bot_token=_env("BOT_TOKEN"),
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        database_url=_env("DATABASE_URL", "queues.db"),
        log_level=_env("LOG_LEVEL", "INFO"),
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    )



def load_premium_config() -> PremiumConfig:
    return PremiumConfig(
        api_id=int(_env("API_ID")),
        api_hash=_env("API_HASH"),
        session_name=_env("SESSION_NAME", "premium_session"),
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        log_level=_env("LOG_LEVEL", "INFO"),
    )



def load_bridge_config() -> BridgeConfig:
    return BridgeConfig(
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        host=_env("BRIDGE_HOST", "0.0.0.0"),
        port=int(_env("BRIDGE_PORT", "8765")),
        health_port=int(_env("HEALTH_PORT", "8080")),
        log_level=_env("LOG_LEVEL", "INFO"),
    )
