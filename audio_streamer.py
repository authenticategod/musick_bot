from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from yt_dlp import YoutubeDL


@dataclass
class AudioSource:
    url: str
    title: str
    duration: int | None
    metadata: dict[str, Any]


class AudioStreamer:
    def __init__(self) -> None:
        self._ytdl = YoutubeDL(
            {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "default_search": "auto",
            }
        )

    async def resolve(self, query: str) -> AudioSource:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, lambda: self._ytdl.extract_info(query, download=False))
        if "entries" in info:
            info = info["entries"][0]
        return AudioSource(
            url=info["url"],
            title=info.get("title") or "Unknown",
            duration=info.get("duration"),
            metadata={
                "webpage_url": info.get("webpage_url"),
                "uploader": info.get("uploader"),
                "thumbnail": info.get("thumbnail"),
            },
        )

    async def normalize_volume(self, input_path: str, output_path: str) -> None:
        raise NotImplementedError("Volume normalization should be implemented with ffmpeg")
