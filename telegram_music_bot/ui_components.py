"""UI components for inline keyboards and status displays."""
from __future__ import annotations

from dataclasses import dataclass

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


@dataclass
class PlaybackStatus:
    title: str
    position: int
    duration: int
    is_playing: bool

    def progress_bar(self, length: int = 20) -> str:
        if self.duration <= 0:
            return "".ljust(length, "—")
        filled = int((self.position / self.duration) * length)
        filled = min(max(filled, 0), length)
        return "█" * filled + "—" * (length - filled)


class UIComponents:
    @staticmethod
    def playback_controls(is_playing: bool) -> InlineKeyboardMarkup:
        play_pause = "⏸" if is_playing else "▶️"
        keyboard = [
            [
                InlineKeyboardButton(play_pause, callback_data="toggle"),
                InlineKeyboardButton("⏭", callback_data="skip"),
                InlineKeyboardButton("⏹", callback_data="stop"),
            ],
            [
                InlineKeyboardButton("🔉", callback_data="volume_down"),
                InlineKeyboardButton("🔊", callback_data="volume_up"),
            ],
            [InlineKeyboardButton("📃 Queue", callback_data="queue")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def queue_controls() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔁 Refresh", callback_data="queue_refresh")],
            [InlineKeyboardButton("🗑 Clear", callback_data="queue_clear")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def status_message(status: PlaybackStatus) -> str:
        state = "Playing" if status.is_playing else "Paused"
        bar = status.progress_bar()
        return f"{state}: {status.title}\n{bar} {status.position}/{status.duration}s"
