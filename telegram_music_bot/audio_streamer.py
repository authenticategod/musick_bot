"""Audio processing and extraction helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL


@dataclass
class AudioSource:
    title: str
    url: str
    local_path: Path
    duration: int | None


class AudioStreamer:
    def __init__(self, cache_path: str) -> None:
        self._cache_path = Path(cache_path)
        self._cache_path.mkdir(parents=True, exist_ok=True)

    def prepare(self, url: str) -> AudioSource:
        options: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": str(self._cache_path / "%(id)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return AudioSource(
            title=info.get("title", "Unknown"),
            url=url,
            local_path=Path(filename),
            duration=info.get("duration"),
        )
