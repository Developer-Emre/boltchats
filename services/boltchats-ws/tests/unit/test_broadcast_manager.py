import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.managers.broadcast_manager import BroadcastManager


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.publish = AsyncMock()
    pubsub = MagicMock()
    pubsub.psubscribe = AsyncMock()
    pubsub.punsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    redis.pubsub = MagicMock(return_value=pubsub)
    return redis


@pytest.fixture
def manager(mock_redis) -> BroadcastManager:
    return BroadcastManager(mock_redis)


@pytest.mark.asyncio
async def test_publish_uses_room_channel_prefix(manager, mock_redis):
    await manager.publish("room_1", '{"type":"message"}')
    mock_redis.publish.assert_called_once_with("room:room_1", '{"type":"message"}')


@pytest.mark.asyncio
async def test_start_subscribes_to_pattern(manager):
    callback = AsyncMock()
    with patch.object(manager, "_listen", new_callable=AsyncMock):
        await manager.start(callback)
    manager._pubsub.psubscribe.assert_called_once_with("room:*")


@pytest.mark.asyncio
async def test_stop_cancels_listen_task(manager):
    async def endless():
        await asyncio.sleep(999)

    manager._listen_task = asyncio.create_task(endless())
    await manager.stop()
    assert manager._listen_task.cancelled()


@pytest.mark.asyncio
async def test_listen_routes_pmessages_to_callback(manager):
    callback = AsyncMock()
    messages = [
        {"type": "psubscribe", "channel": "room:*", "data": 1},
        {"type": "pmessage", "channel": "room:abc", "data": '{"type":"message"}'},
        {"type": "pmessage", "channel": "room:xyz", "data": '{"type":"pong"}'},
    ]

    async def fake_listen():
        for m in messages:
            yield m

    manager._pubsub.listen = fake_listen
    await manager._listen(callback)

    assert callback.call_count == 2
    callback.assert_any_call("abc", '{"type":"message"}')
    callback.assert_any_call("xyz", '{"type":"pong"}')


@pytest.mark.asyncio
async def test_listen_ignores_non_pmessages(manager):
    callback = AsyncMock()
    messages = [
        {"type": "subscribe", "channel": "room:a", "data": 1},
        {"type": "psubscribe", "channel": "room:*", "data": 1},
    ]

    async def fake_listen():
        for m in messages:
            yield m

    manager._pubsub.listen = fake_listen
    await manager._listen(callback)
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_stop_without_task_is_safe(manager):
    manager._listen_task = None
    await manager.stop()  # must not raise
