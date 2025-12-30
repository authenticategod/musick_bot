from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp
import aiohttp.web
import redis.asyncio as redis
import websockets

from config import load_bridge_config


class BridgeServer:
    def __init__(self, redis_url: str) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def publish(self, channel: str, payload: dict[str, Any]) -> None:
        await self._redis.publish(channel, json.dumps(payload))

    async def handle_ws(self, websocket: websockets.WebSocketServerProtocol) -> None:
        async for message in websocket:
            payload = json.loads(message)
            action = payload.get("action")
            if not action:
                await websocket.send(json.dumps({"error": "missing action"}))
                continue
            await self.publish("music_actions", payload)
            await websocket.send(json.dumps({"status": "queued", "action": action}))


async def health_handler(_: aiohttp.web.Request) -> aiohttp.web.Response:
    return aiohttp.web.json_response({"status": "ok"})


async def start_health_server(port: int) -> aiohttp.web.AppRunner:
    app = aiohttp.web.Application()
    app.add_routes([aiohttp.web.get("/health", health_handler)])
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner


async def main() -> None:
    config = load_bridge_config()
    logging.basicConfig(level=config.log_level)
    bridge = BridgeServer(config.redis_url)

    health_runner = await start_health_server(config.health_port)

    async with websockets.serve(bridge.handle_ws, config.host, config.port):
        logging.info("Bridge server running on %s:%s", config.host, config.port)
        await asyncio.Future()

    await health_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
