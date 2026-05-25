import json

import pytest

from app.constants.ws_codes import REDIS_KEY_PRESENCE_ONLINE, REDIS_PREFIX_PRESENCE_ROOM, REDIS_QUEUE_MESSAGES


@pytest.mark.integration
def test_join_room_updates_presence_in_redis(client, valid_token, sync_redis):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong — join processed

        members = sync_redis.smembers(f"{REDIS_PREFIX_PRESENCE_ROOM}room_1")
        assert "user_001" in members

        online = sync_redis.smembers(REDIS_KEY_PRESENCE_ONLINE)
        assert "user_001" in online


@pytest.mark.integration
def test_leave_room_removes_from_room_presence(client, valid_token, sync_redis):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "leave_room", "room_id": "room_1"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

        members = sync_redis.smembers(f"{REDIS_PREFIX_PRESENCE_ROOM}room_1")
        assert "user_001" not in members


@pytest.mark.integration
def test_disconnect_removes_from_global_presence(client, valid_token, monkeypatch):
    from unittest.mock import AsyncMock
    from app.managers.presence_manager import PresenceManager

    user_offline_calls: list[tuple[str, list[str]]] = []
    original = PresenceManager.user_offline

    async def spy_user_offline(self: PresenceManager, user_id: str, room_ids: list[str]) -> None:
        user_offline_calls.append((user_id, list(room_ids)))
        await original(self, user_id, room_ids)

    monkeypatch.setattr(PresenceManager, "user_offline", spy_user_offline)

    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong — join processed

    # WS close triggers the finally block which calls user_offline.
    # With TestClient the background task is joined when the ws context exits.
    assert ("user_001", ["room_1"]) in user_offline_calls


@pytest.mark.integration
def test_message_enqueued_in_redis_queue(client, valid_token, sync_redis):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "message", "room_id": "room_1", "content": "hello world"})
        # Ping ensures message handler has completed before we check
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

    queue_len = sync_redis.llen(REDIS_QUEUE_MESSAGES)
    assert queue_len == 1

    raw = sync_redis.lrange(REDIS_QUEUE_MESSAGES, 0, -1)
    payload = json.loads(raw[0])
    assert payload["content"] == "hello world"
    assert payload["room_id"] == "room_1"
    assert payload["sender_id"] == "user_001"


@pytest.mark.integration
def test_message_not_queued_when_not_room_member(client, valid_token, sync_redis):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        # No join_room — send message directly
        ws.send_json({"type": "message", "room_id": "room_1", "content": "dropped"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

    queue_len = sync_redis.llen(REDIS_QUEUE_MESSAGES)
    assert queue_len == 0


@pytest.mark.integration
def test_rate_limit_sends_error_after_limit_exceeded(client, monkeypatch):
    from app.core.config import get_settings, Settings

    # Override rate limit to 2 messages/second
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(rate_limit_messages_per_second=2, secret_key=get_settings().secret_key),
    )

    from tests.conftest import make_token
    token = make_token("user_rl")

    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        for _ in range(5):
            ws.send_json({"type": "ping"})

        responses = [ws.receive_json() for _ in range(5)]

    error_count = sum(1 for r in responses if r.get("type") == "error")
    assert error_count >= 1


@pytest.mark.integration
def test_multiple_messages_all_enqueued(client, valid_token, sync_redis):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        for i in range(3):
            ws.send_json({"type": "message", "room_id": "room_1", "content": f"msg {i}"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

    queue_len = sync_redis.llen(REDIS_QUEUE_MESSAGES)
    assert queue_len == 3
