from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


@dataclass
class PlaybackStatus:
    title: str
    progress: int
    duration: int
    is_paused: bool


def playback_controls() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏮️", callback_data="rewind"),
                InlineKeyboardButton("⏯️", callback_data="pause"),
                InlineKeyboardButton("⏭️", callback_data="skip"),
                InlineKeyboardButton("⏹️", callback_data="stop"),
            ],
            [
                InlineKeyboardButton("🔉", callback_data="vol_down"),
                InlineKeyboardButton("🔊", callback_data="vol_up"),
                InlineKeyboardButton("📝 Queue", callback_data="queue"),
            ],
            [InlineKeyboardButton("▶️ Resume", callback_data="resume")],
        ]
    )


def render_progress_bar(status: PlaybackStatus, width: int = 20) -> str:
    if status.duration <= 0:
        return "".ljust(width, "─")
    filled = int((status.progress / status.duration) * width)
    filled = min(max(filled, 0), width)
    return "▰" * filled + "▱" * (width - filled)


def queue_list(items: Iterable[str]) -> str:
    lines = [f"{idx}. {item}" for idx, item in enumerate(items, start=1)]
    return "\n".join(lines) if lines else "Queue is empty."
