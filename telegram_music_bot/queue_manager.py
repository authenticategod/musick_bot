"""Queue persistence and management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import aiosqlite


@dataclass
class QueueItem:
    chat_id: int
    user_id: int
    title: str
    url: str
    requested_at: datetime


class QueueManager:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    requested_at TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def add(self, item: QueueItem) -> None:
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute(
                """
                INSERT INTO queue (chat_id, user_id, title, url, requested_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.chat_id,
                    item.user_id,
                    item.title,
                    item.url,
                    item.requested_at.isoformat(),
                ),
            )
            await db.commit()

    async def list(self, chat_id: int) -> list[QueueItem]:
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute(
                """
                SELECT chat_id, user_id, title, url, requested_at
                FROM queue
                WHERE chat_id = ?
                ORDER BY id ASC
                """,
                (chat_id,),
            )
            rows = await cursor.fetchall()
        return [
            QueueItem(
                chat_id=row[0],
                user_id=row[1],
                title=row[2],
                url=row[3],
                requested_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    async def pop_next(self, chat_id: int) -> QueueItem | None:
        async with aiosqlite.connect(self._database_path) as db:
            cursor = await db.execute(
                """
                SELECT id, chat_id, user_id, title, url, requested_at
                FROM queue
                WHERE chat_id = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (chat_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            await db.execute("DELETE FROM queue WHERE id = ?", (row[0],))
            await db.commit()

        return QueueItem(
            chat_id=row[1],
            user_id=row[2],
            title=row[3],
            url=row[4],
            requested_at=datetime.fromisoformat(row[5]),
        )

    async def clear(self, chat_id: int) -> None:
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
            await db.commit()

    async def seed(self, chat_id: int, items: Iterable[QueueItem]) -> None:
        async with aiosqlite.connect(self._database_path) as db:
            await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
            await db.executemany(
                """
                INSERT INTO queue (chat_id, user_id, title, url, requested_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.chat_id,
                        item.user_id,
                        item.title,
                        item.url,
                        item.requested_at.isoformat(),
                    )
                    for item in items
                ],
            )
            await db.commit()
