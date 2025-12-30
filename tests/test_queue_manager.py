import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from queue_manager import QueueItem, QueueManager  # noqa: E402


@pytest.mark.asyncio
async def test_enqueue_and_pop(tmp_path):
    db_path = tmp_path / "queues.db"
    manager = QueueManager(str(db_path))
    await manager.setup()

    item = QueueItem(title="Song", url="http://example.com", requested_by=1)
    await manager.enqueue(123, item)
    queued = await manager.list_queue(123)

    assert len(queued) == 1
    assert queued[0].title == "Song"

    next_item = await manager.pop_next(123)
    assert next_item is not None
    assert next_item.title == "Song"
    assert await manager.list_queue(123) == []
