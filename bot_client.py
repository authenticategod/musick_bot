from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as redis
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from audio_streamer import AudioStreamer
from config import load_bot_config
from queue_manager import QueueItem, QueueManager
from ui_components import PlaybackStatus, playback_controls, queue_list, render_progress_bar


class BridgeClient:
    def __init__(self, redis_url: str) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)

    async def send_action(self, payload: dict[str, Any]) -> None:
        await self._redis.publish("music_actions", json.dumps(payload))


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /play <song name or URL>")
        return
    streamer: AudioStreamer = context.application.bot_data["streamer"]
    queue: QueueManager = context.application.bot_data["queue"]
    bridge: BridgeClient = context.application.bot_data["bridge"]

    source = await streamer.resolve(query)
    item = QueueItem(title=source.title, url=source.url, requested_by=update.effective_user.id)
    await queue.enqueue(update.effective_chat.id, item)

    now_playing: dict[int, QueueItem] = context.application.bot_data.setdefault("now_playing", {})
    if update.effective_chat.id not in now_playing:
        next_item = await queue.pop_next(update.effective_chat.id)
        if next_item:
            now_playing[update.effective_chat.id] = next_item
            await bridge.send_action(
                {
                    "action": "play",
                    "chat_id": update.effective_chat.id,
                    "user_id": update.effective_user.id,
                    "metadata": {"title": next_item.title, "url": next_item.url},
                }
            )
    await update.message.reply_text(
        f"Queued: {source.title}\n{render_progress_bar(PlaybackStatus(source.title, 0, source.duration or 1, False))}",
        reply_markup=playback_controls(),
    )


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    queue: QueueManager = context.application.bot_data["queue"]
    items = await queue.list_queue(update.effective_chat.id)
    await update.message.reply_text(queue_list([item.title for item in items]))


async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return
    bridge: BridgeClient = context.application.bot_data["bridge"]
    await bridge.send_action(
        {"action": "pause", "chat_id": update.effective_chat.id, "user_id": update.effective_user.id}
    )
    await update.message.reply_text("Playback paused.")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return
    bridge: BridgeClient = context.application.bot_data["bridge"]
    await bridge.send_action(
        {"action": "resume", "chat_id": update.effective_chat.id, "user_id": update.effective_user.id}
    )
    await update.message.reply_text("Playback resumed.")


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return
    bridge: BridgeClient = context.application.bot_data["bridge"]
    queue: QueueManager = context.application.bot_data["queue"]
    now_playing: dict[int, QueueItem] = context.application.bot_data.setdefault("now_playing", {})

    await bridge.send_action(
        {"action": "skip", "chat_id": update.effective_chat.id, "user_id": update.effective_user.id}
    )

    next_item = await queue.pop_next(update.effective_chat.id)
    if next_item:
        now_playing[update.effective_chat.id] = next_item
        await bridge.send_action(
            {
                "action": "play",
                "chat_id": update.effective_chat.id,
                "user_id": update.effective_user.id,
                "metadata": {"title": next_item.title, "url": next_item.url},
            }
        )
        await update.message.reply_text(f"Now playing: {next_item.title}")
        return

    now_playing.pop(update.effective_chat.id, None)
    await update.message.reply_text("Queue ended.")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user:
        return
    bridge: BridgeClient = context.application.bot_data["bridge"]
    queue: QueueManager = context.application.bot_data["queue"]
    now_playing: dict[int, QueueItem] = context.application.bot_data.setdefault("now_playing", {})

    await queue.clear(update.effective_chat.id)
    now_playing.pop(update.effective_chat.id, None)
    await bridge.send_action(
        {"action": "stop", "chat_id": update.effective_chat.id, "user_id": update.effective_user.id}
    )
    await update.message.reply_text("Stopped playback and cleared the queue.")


async def handle_controls(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query or not update.effective_chat or not update.effective_user:
        return
    action = update.callback_query.data
    bridge: BridgeClient = context.application.bot_data["bridge"]
    await bridge.send_action(
        {"action": action, "chat_id": update.effective_chat.id, "user_id": update.effective_user.id}
    )
    await update.callback_query.answer()


async def main() -> None:
    config = load_bot_config()
    logging.basicConfig(level=config.log_level)

    application = Application.builder().token(config.bot_token).build()
    queue = QueueManager(config.database_url)
    await queue.setup()

    application.bot_data["queue"] = queue
    application.bot_data["streamer"] = AudioStreamer()
    application.bot_data["bridge"] = BridgeClient(config.redis_url)

    application.add_handler(CommandHandler("play", play))
    application.add_handler(CommandHandler("pause", pause))
    application.add_handler(CommandHandler("resume", resume))
    application.add_handler(CommandHandler("skip", skip))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CallbackQueryHandler(handle_controls))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
