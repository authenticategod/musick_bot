from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
from telethon import TelegramClient

from config import load_premium_config


@dataclass
class PlaybackState:
    chat_id: int
    title: str
    source_url: str
    is_playing: bool
    position: int = 0
    volume: int = 100


class PremiumMusicPlayer:
    def __init__(self, session_name: str, api_id: int, api_hash: str, redis_url: str) -> None:
        self.client = TelegramClient(session_name, api_id, api_hash)
        self._calls = PyTgCalls(self.client)
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._state: dict[int, PlaybackState] = {}

    async def start(self) -> None:
        await self.client.start()
        await self._calls.start()
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe("music_actions")
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            payload = json.loads(message["data"])
            await self._handle_action(payload)

    async def _handle_action(self, payload: dict[str, Any]) -> None:
        action = payload.get("action")
        chat_id = payload.get("chat_id")
        if not chat_id or not action:
            return
        if action == "play":
            await self.join_and_play(chat_id, payload.get("metadata", {}).get("url", ""))
        elif action == "pause":
            await self.pause(chat_id)
        elif action == "resume":
            await self.resume(chat_id)
        elif action == "skip":
            await self.skip(chat_id)
        elif action == "stop":
            await self.stop(chat_id)
        elif action == "rewind":
            await self.rewind(chat_id)
        elif action == "vol_up":
            await self.adjust_volume(chat_id, 10)
        elif action == "vol_down":
            await self.adjust_volume(chat_id, -10)

    async def join_and_play(self, chat_id: int, audio_url: str) -> None:
        if not audio_url:
            logging.warning("No audio URL provided for chat %s", chat_id)
            return
        logging.info("Joining voice chat %s for playback", chat_id)
        state = PlaybackState(
            chat_id=chat_id,
            title=audio_url,
            source_url=audio_url,
            is_playing=True,
        )
        self._state[chat_id] = state
        await self._calls.join_group_call(
            chat_id,
            AudioPiped(audio_url, HighQualityAudio()),
        )

    async def pause(self, chat_id: int) -> None:
        state = self._state.get(chat_id)
        if not state:
            return
        if state.is_playing:
            await self._calls.pause_stream(chat_id)
            state.is_playing = False
        else:
            await self._calls.resume_stream(chat_id)
            state.is_playing = True

    async def resume(self, chat_id: int) -> None:
        state = self._state.get(chat_id)
        if not state:
            return
        await self._calls.resume_stream(chat_id)
        state.is_playing = True

    async def skip(self, chat_id: int) -> None:
        logging.info("Skipping current track in %s", chat_id)
        await self.stop(chat_id)

    async def stop(self, chat_id: int) -> None:
        if chat_id in self._state:
            await self._calls.leave_group_call(chat_id)
            self._state.pop(chat_id, None)

    async def rewind(self, chat_id: int) -> None:
        state = self._state.get(chat_id)
        if not state:
            return
        await self.join_and_play(chat_id, state.source_url)

    async def adjust_volume(self, chat_id: int, delta: int) -> None:
        state = self._state.get(chat_id)
        if not state:
            return
        state.volume = min(200, max(0, state.volume + delta))
        await self._calls.change_volume_call(chat_id, state.volume)


async def main() -> None:
    config = load_premium_config()
    logging.basicConfig(level=config.log_level)
    player = PremiumMusicPlayer(
        session_name=config.session_name,
        api_id=config.api_id,
        api_hash=config.api_hash,
        redis_url=config.redis_url,
    )
    await player.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
