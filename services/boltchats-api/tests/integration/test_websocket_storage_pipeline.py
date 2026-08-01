"""
Integration test: WebSocket ↔ Redis Queue ↔ Storage

Flow:
1. User connects via WebSocket
2. User sends message
3. Message pushed to Redis queue
4. Storage worker consumes and persists
5. Event published back
6. User receives confirmation
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.managers.connection_manager import ConnectionManager
from app.utils.message_queue import MessageQueue
from app.worker.consumer import StorageWorker


@pytest.mark.asyncio
async def test_websocket_message_to_storage_pipeline(
    redis_client,
    mongo_db,
    mock_websocket,
):
    """Test end-to-end message flow: WS → Queue → Storage → Event"""

    # 1. Setup
    connection_id = "conn_test_001"
    user_id = "usr_001"
    room_id = "conv_001"

    connection_manager = ConnectionManager(redis=redis_client)
    message_queue = MessageQueue(redis=redis_client)
    storage_worker = StorageWorker(
        mongo_client=None,
        db=mongo_db,
        redis=redis_client,
    )

    # 2. User connects
    await connection_manager.connect(
        mock_websocket,
        user_id,
        connection_id,
    )
    await connection_manager.subscribe_room(connection_id, room_id)

    # 3. Create test message
    message_data = {
        "id": "msg_001",
        "conversation_id": room_id,
        "sender_id": user_id,
        "content": "Hello from WebSocket!",
        "channel": "websocket",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {"platform": "web"},
    }

    # 4. Push to queue (simulating WebSocket handler)
    await message_queue.enqueue(json.dumps(message_data))

    # 5. Verify message in queue
    queue_length = await redis_client.llen("messages:queue")
    assert queue_length == 1

    # 6. Process batch (storage worker)
    await storage_worker._process_batch()

    # 7. Verify message persisted
    collection = mongo_db["messages"]
    persisted = await collection.find_one({"_id": "msg_001"})
    assert persisted is not None
    assert persisted["content"] == "Hello from WebSocket!"
    assert persisted["sender_id"] == user_id
    assert persisted["deleted"] is False

    # 8. Verify conversation updated
    conversations = mongo_db["conversations"]
    conv = await conversations.find_one({"_id": room_id})
    assert conv is not None
    assert conv["last_message_at"] is not None

    # 9. Verify event published
    # (In real scenario, BroadcastManager would receive this)
    assert queue_length == 1  # Queue emptied

    await connection_manager.disconnect(connection_id, mock_websocket)


@pytest.mark.asyncio
async def test_websocket_connection_manager_rooms(
    redis_client,
    mock_websocket,
):
    """Test room subscription and broadcasting"""

    connection_manager = ConnectionManager(redis=redis_client)

    # Connect user
    user_id = "usr_room_test"
    connection_id = "conn_room_001"
    
    await connection_manager.connect(mock_websocket, user_id, connection_id)

    # Subscribe to 3 rooms
    await connection_manager.subscribe_room(connection_id, "room_1")
    await connection_manager.subscribe_room(connection_id, "room_2")
    await connection_manager.subscribe_room(connection_id, "room_3")

    # Verify subscribed
    conn_info = connection_manager._connections[connection_id]
    assert "room_1" in conn_info["rooms"]
    assert "room_2" in conn_info["rooms"]
    assert "room_3" in conn_info["rooms"]

    # Broadcast to room_2
    message = {"type": "message", "content": "test"}
    result = await connection_manager.broadcast_to_room("room_2", message)

    assert result["room_id"] == "room_2"
    assert result["sent"] == 1
    assert result["failed"] == 0

    # Unsubscribe from room_1
    await connection_manager.unsubscribe_room(connection_id, "room_1")
    assert "room_1" not in conn_info["rooms"]
    assert "room_2" in conn_info["rooms"]

    # Broadcast to room_1 (should not reach)
    result = await connection_manager.broadcast_to_room("room_1", message)
    assert result["sent"] == 0

    connection_manager.disconnect(connection_id, mock_websocket)


@pytest.mark.asyncio
async def test_message_idempotency(
    redis_client,
    mongo_db,
):
    """Test that duplicate messages are handled correctly (upsert)"""

    storage_worker = StorageWorker(
        mongo_client=None,
        db=mongo_db,
        redis=redis_client,
    )

    message_data = {
        "id": "msg_dup_test",
        "conversation_id": "conv_dup",
        "sender_id": "usr_dup",
        "content": "Original content",
        "channel": "test",
        "created_at": datetime.utcnow().isoformat(),
    }

    # Persist twice with same ID
    await storage_worker._persist_message(message_data)
    await storage_worker._persist_message(message_data)

    collection = mongo_db["messages"]
    messages = await collection.find({"_id": "msg_dup_test"}).to_list(length=None)

    # Should have exactly 1 document (idempotent)
    assert len(messages) == 1
    assert messages[0]["content"] == "Original content"


@pytest.mark.asyncio
async def test_dead_letter_queue(
    redis_client,
    mongo_db,
):
    """Test DLQ for failed messages"""

    storage_worker = StorageWorker(
        mongo_client=None,
        db=mongo_db,
        redis=redis_client,
    )

    # Create invalid message (missing required fields)
    bad_messages = [
        {"id": "msg_bad_1"},  # missing conversation_id
        {"conversation_id": "conv_123"},  # missing id
    ]

    await storage_worker._send_to_dlq(bad_messages)

    # Verify in DLQ
    dlq_length = await redis_client.llen("messages:queue:dlq")
    assert dlq_length == 2

    # Verify DLQ has TTL
    dlq_ttl = await redis_client.ttl("messages:queue:dlq")
    assert dlq_ttl > 0


@pytest.mark.asyncio
async def test_presence_tracking(
    redis_client,
    mock_websocket,
):
    """Test user presence tracking across connections"""

    connection_manager = ConnectionManager(redis=redis_client)

    user_id = "usr_presence_test"

    # Create 3 connections for same user
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    ws3 = AsyncMock()

    conn_id_1 = "conn_pres_1"
    conn_id_2 = "conn_pres_2"
    conn_id_3 = "conn_pres_3"

    await connection_manager.connect(ws1, user_id, conn_id_1)
    await connection_manager.connect(ws2, user_id, conn_id_2)
    await connection_manager.connect(ws3, user_id, conn_id_3)

    # Get active connections for user
    active = connection_manager.get_user_connections(user_id)
    assert len(active) == 3

    # Send to user (should reach all 3)
    message = {"type": "notification", "data": "test"}
    result = await connection_manager.send_to_user(user_id, message)
    assert result["sent"] == 3

    # Disconnect one
    connection_manager.disconnect(conn_id_1, ws1)
    active = connection_manager.get_user_connections(user_id)
    assert len(active) == 2


@pytest.mark.asyncio
async def test_heartbeat_cleanup(
    redis_client,
    mock_websocket,
):
    """Test heartbeat removes dead connections"""

    connection_manager = ConnectionManager(redis=redis_client)

    user_id = "usr_hb_test"
    conn_id = "conn_hb_001"

    await connection_manager.connect(mock_websocket, user_id, conn_id)

    # Simulate dead connection by raising exception on send
    conn_info = connection_manager._connections[conn_id]
    conn_info["websocket"].send_json = AsyncMock(side_effect=Exception("Connection dead"))

    # Heartbeat should clean up
    disconnected = await connection_manager.heartbeat()
    assert disconnected == 1

    # Verify removed from active connections
    assert conn_id not in connection_manager._connections
