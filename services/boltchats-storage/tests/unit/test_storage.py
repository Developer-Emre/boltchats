import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pymongo.errors import PyMongoError

from app.storage import MessageRepository


SAMPLE_PAYLOAD = {
    "room_id": "room-1",
    "sender_id": "user-42",
    "content": "Hello, world!",
    "created_at": "2026-05-26T10:00:00+00:00",
}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_success(mock_db):
    repo = MessageRepository(mock_db)
    await repo.insert(dict(SAMPLE_PAYLOAD))

    doc = await mock_db["messages"].find_one({"room_id": "room-1"})
    assert doc is not None
    assert doc["sender_id"] == "user-42"
    assert doc["content"] == "Hello, world!"


# ---------------------------------------------------------------------------
# Error case — MongoDB raises on first attempt, succeeds on retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_retries_on_failure(mock_collection):
    mock_collection.insert_one.side_effect = [
        PyMongoError("transient error"),
        None,  # second attempt succeeds
    ]

    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=mock_collection)

    repo = MessageRepository(db)

    with patch("app.storage.asyncio.sleep", new_callable=AsyncMock):
        await repo.insert(dict(SAMPLE_PAYLOAD))

    assert mock_collection.insert_one.call_count == 2


# ---------------------------------------------------------------------------
# Error case — all retries exhausted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_raises_after_all_retries_exhausted(mock_collection):
    mock_collection.insert_one.side_effect = PyMongoError("persistent error")

    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=mock_collection)

    repo = MessageRepository(db)

    with patch("app.storage.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(RuntimeError, match="MongoDB insert failed after retries"):
            await repo.insert(dict(SAMPLE_PAYLOAD))

    assert mock_collection.insert_one.call_count == 3  # default max_retries


# ---------------------------------------------------------------------------
# Edge case — empty content is still persisted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_empty_content(mock_db):
    repo = MessageRepository(mock_db)
    payload = {**SAMPLE_PAYLOAD, "content": ""}
    await repo.insert(payload)

    doc = await mock_db["messages"].find_one({"room_id": "room-1"})
    assert doc is not None
    assert doc["content"] == ""
