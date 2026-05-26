import asyncio
import json

import pytest
import pytest_asyncio

from app.consumer import consume
from app.storage import MessageRepository

pytestmark = pytest.mark.integration


SAMPLE_MESSAGE = {
    "room_id": "room-1",
    "sender_id": "user-42",
    "content": "Integration test message",
    "created_at": "2026-05-26T10:00:00+00:00",
}


# ---------------------------------------------------------------------------
# Happy path — message consumed from queue and persisted in MongoDB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_consumer_persists_message(mock_redis, mock_db):
    await mock_redis.lpush("messages:queue", json.dumps(SAMPLE_MESSAGE))

    repo = MessageRepository(mock_db)

    task = asyncio.create_task(consume(mock_redis, repo))
    await asyncio.sleep(0.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    doc = await mock_db["messages"].find_one({"room_id": "room-1"})
    assert doc is not None
    assert doc["sender_id"] == "user-42"
    assert doc["content"] == "Integration test message"


# ---------------------------------------------------------------------------
# Error case — malformed JSON is skipped without crashing the consumer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_consumer_skips_malformed_json(mock_redis, mock_db):
    await mock_redis.lpush("messages:queue", "not-valid-json")
    await mock_redis.lpush("messages:queue", json.dumps(SAMPLE_MESSAGE))

    repo = MessageRepository(mock_db)

    task = asyncio.create_task(consume(mock_redis, repo))
    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Valid message still persisted despite the malformed one
    doc = await mock_db["messages"].find_one({"room_id": "room-1"})
    assert doc is not None


# ---------------------------------------------------------------------------
# Edge case — multiple messages consumed in order
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_consumer_processes_multiple_messages(mock_redis, mock_db):
    messages = [
        {**SAMPLE_MESSAGE, "content": f"msg-{i}"}
        for i in range(3)
    ]
    for msg in messages:
        await mock_redis.lpush("messages:queue", json.dumps(msg))

    repo = MessageRepository(mock_db)

    task = asyncio.create_task(consume(mock_redis, repo))
    await asyncio.sleep(0.3)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    count = await mock_db["messages"].count_documents({"room_id": "room-1"})
    assert count == 3
