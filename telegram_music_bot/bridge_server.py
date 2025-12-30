"""Redis-based bridge between the bot and premium account."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

import redis.asyncio as redis

from telegram_music_bot.config import Config


@dataclass
class BridgeMessage:
    action: str
    chat_id: int
    user_id: int
    payload: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(
            {
                "action": self.action,
                "chat_id": self.chat_id,
                "user_id": self.user_id,
                "payload": self.payload,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> "BridgeMessage":
        data = json.loads(raw)
        return cls(
            action=data["action"],
            chat_id=int(data["chat_id"]),
            user_id=int(data["user_id"]),
            payload=data.get("payload", {}),
        )


class RedisBridge:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._redis = redis.from_url(config.redis_url, decode_responses=True)

    async def publish(self, message: BridgeMessage) -> None:
        await self._redis.publish(self._config.bridge_channel, message.to_json())

    async def subscribe(self) -> AsyncIterator[BridgeMessage]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._config.bridge_channel)
        try:
            async for raw in pubsub.listen():
                if raw.get("type") != "message":
                    continue
                data = raw.get("data")
                if not data:
                    continue
                yield BridgeMessage.from_json(data)
        finally:
            await pubsub.unsubscribe(self._config.bridge_channel)
            await pubsub.close()

    async def close(self) -> None:
        await self._redis.close()


async def run_healthcheck_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.read(1024)
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle, host, port)
    async with server:
        await server.serve_forever()


async def main() -> None:
    config = Config.from_env()
    bridge = RedisBridge(config)
    try:
        await run_healthcheck_server()
    finally:
        await bridge.close()


if __name__ == "__main__":
    asyncio.run(main())
