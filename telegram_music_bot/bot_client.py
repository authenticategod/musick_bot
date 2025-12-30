"""Bot account command interface."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from telegram_music_bot.bridge_server import BridgeMessage, RedisBridge
from telegram_music_bot.config import Config
from telegram_music_bot.queue_manager import QueueItem, QueueManager
from telegram_music_bot.ui_components import PlaybackStatus, UIComponents


class BotClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._bridge = RedisBridge(config)
        self._queues = QueueManager(config.database_path)

    async def start(self) -> None:
        await self._queues.initialize()
        application = Application.builder().token(self._config.bot_token).build()
        application.add_handler(CommandHandler("play", self.play))
        application.add_handler(CommandHandler("pause", self.pause))
        application.add_handler(CommandHandler("skip", self.skip))
        application.add_handler(CommandHandler("queue", self.queue))
        application.add_handler(CallbackQueryHandler(self.callbacks))

        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        await application.updater.wait()

    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat or not update.effective_user:
            return
        if not context.args:
            await update.message.reply_text("Provide a URL or search query.")
            return

        query = " ".join(context.args)
        item = QueueItem(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id,
            title=query,
            url=query,
            requested_at=datetime.utcnow(),
        )
        await self._queues.add(item)
        await self._bridge.publish(
            BridgeMessage(
                action="play",
                chat_id=item.chat_id,
                user_id=item.user_id,
                payload={"query": query},
            )
        )
        await update.message.reply_text(
            f"Queued: {query}",
            reply_markup=UIComponents.playback_controls(is_playing=True),
        )

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._simple_action(update, "pause")

    async def skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._simple_action(update, "skip")

    async def queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat or not update.message:
            return
        await update.message.chat.send_action(ChatAction.TYPING)
        items = await self._queues.list(update.effective_chat.id)
        if not items:
            await update.message.reply_text("Queue is empty.")
            return
        lines = [f"{idx + 1}. {item.title}" for idx, item in enumerate(items)]
        await update.message.reply_text(
            "\n".join(lines), reply_markup=UIComponents.queue_controls()
        )

    async def callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.callback_query or not update.effective_chat:
            return
        action = update.callback_query.data
        await update.callback_query.answer()
        if action == "queue":
            await self.queue(update, context)
            return
        if action == "queue_refresh":
            await self.queue(update, context)
            return
        if action == "queue_clear":
            await self._queues.clear(update.effective_chat.id)
            await update.callback_query.edit_message_text("Queue cleared.")
            return
        await self._bridge.publish(
            BridgeMessage(
                action=action,
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id if update.effective_user else 0,
                payload={},
            )
        )
        status = PlaybackStatus(
            title="Pending",
            position=0,
            duration=0,
            is_playing=action != "toggle",
        )
        await update.callback_query.edit_message_text(
            UIComponents.status_message(status),
            reply_markup=UIComponents.playback_controls(status.is_playing),
        )

    async def _simple_action(self, update: Update, action: str) -> None:
        if not update.effective_chat or not update.effective_user:
            return
        await self._bridge.publish(
            BridgeMessage(
                action=action,
                chat_id=update.effective_chat.id,
                user_id=update.effective_user.id,
                payload={},
            )
        )
        if update.message:
            await update.message.reply_text(f"Sent {action} to player.")


async def main() -> None:
    config = Config.from_env()
    bot = BotClient(config)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
