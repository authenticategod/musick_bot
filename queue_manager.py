from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

import aiosqlite


@dataclass
class QueueItem:
    title: str
    url: str
    requested_by: int
    metadata: dict[str, Any] = field(default_factory=dict)


class QueueManager:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    async def setup(self) -> None:
        async with aiosqlite.connect(self._database_url) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS queues (
                    chat_id INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    item_json TEXT NOT NULL,
                    PRIMARY KEY (chat_id, position)
                )
                """
            )
            await db.commit()

    async def enqueue(self, chat_id: int, item: QueueItem) -> None:
        async with aiosqlite.connect(self._database_url) as db:
            cursor = await db.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM queues WHERE chat_id = ?",
                (chat_id,),
            )
            row = await cursor.fetchone()
            position = row[0] if row else 0
            await db.execute(
                "INSERT INTO queues (chat_id, position, item_json) VALUES (?, ?, ?)",
                (chat_id, position, json.dumps(asdict(item))),
            )
            await db.commit()

    async def pop_next(self, chat_id: int) -> QueueItem | None:
        async with aiosqlite.connect(self._database_url) as db:
            cursor = await db.execute(
                "SELECT position, item_json FROM queues WHERE chat_id = ? ORDER BY position ASC LIMIT 1",
                (chat_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            position, item_json = row
            await db.execute(
                "DELETE FROM queues WHERE chat_id = ? AND position = ?",
                (chat_id, position),
            )
            await db.commit()
            payload = json.loads(item_json)
            return QueueItem(**payload)

    async def list_queue(self, chat_id: int) -> list[QueueItem]:
        async with aiosqlite.connect(self._database_url) as db:
            cursor = await db.execute(
                "SELECT item_json FROM queues WHERE chat_id = ? ORDER BY position ASC",
                (chat_id,),
            )
            rows = await cursor.fetchall()
        return [QueueItem(**json.loads(item_json)) for (item_json,) in rows]

    async def clear(self, chat_id: int) -> None:
        async with aiosqlite.connect(self._database_url) as db:
            await db.execute("DELETE FROM queues WHERE chat_id = ?", (chat_id,))
            await db.commit()
