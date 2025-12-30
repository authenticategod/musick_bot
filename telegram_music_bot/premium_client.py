"""Premium account music player."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from telethon import TelegramClient

from telegram_music_bot.audio_streamer import AudioStreamer
from telegram_music_bot.bridge_server import BridgeMessage, RedisBridge
from telegram_music_bot.config import Config


@dataclass
class PlaybackState:
    chat_id: int
    title: str
    is_playing: bool
    position: int
    duration: int | None


class PremiumMusicPlayer:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = TelegramClient("premium_session", config.api_id, config.api_hash)
        self._calls = PyTgCalls(self._client)
        self._bridge = RedisBridge(config)
        self._streamer = AudioStreamer(config.audio_cache_path)
        self._states: dict[int, PlaybackState] = {}

    async def start(self) -> None:
        await self._client.start()
        await self._calls.start()
        await self._listen_bridge()

    async def _listen_bridge(self) -> None:
        async for message in self._bridge.subscribe():
            await self._handle_message(message)

    async def _handle_message(self, message: BridgeMessage) -> None:
        if message.action == "play":
            query = message.payload.get("query", "")
            if not query:
                return
            await self._play(message.chat_id, query)
        elif message.action in {"pause", "toggle"}:
            await self._pause(message.chat_id)
        elif message.action == "skip":
            await self._skip(message.chat_id)
        elif message.action == "stop":
            await self._stop(message.chat_id)

    async def _play(self, chat_id: int, url: str) -> None:
        source = self._streamer.prepare(url)
        await self._calls.join_group_call(
            chat_id,
            AudioPiped(str(source.local_path)),
            stream_type=None,
        )
        self._states[chat_id] = PlaybackState(
            chat_id=chat_id,
            title=source.title,
            is_playing=True,
            position=0,
            duration=source.duration,
        )
        asyncio.create_task(self._progress_loop(chat_id))

    async def _pause(self, chat_id: int) -> None:
        state = self._states.get(chat_id)
        if not state:
            return
        await self._calls.pause_stream(chat_id)
        state.is_playing = False

    async def _skip(self, chat_id: int) -> None:
        await self._calls.leave_group_call(chat_id)
        self._states.pop(chat_id, None)

    async def _stop(self, chat_id: int) -> None:
        await self._calls.leave_group_call(chat_id)
        self._states.pop(chat_id, None)

    async def _progress_loop(self, chat_id: int) -> None:
        while True:
            state = self._states.get(chat_id)
            if not state or not state.is_playing:
                await asyncio.sleep(1)
                if not state:
                    return
                continue
            state.position += 1
            await asyncio.sleep(1)


async def main() -> None:
    config = Config.from_env()
    player = PremiumMusicPlayer(config)
    await player.start()


if __name__ == "__main__":
    asyncio.run(main())
