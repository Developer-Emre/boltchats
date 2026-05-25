import json

import pytest

from app.main import connection_manager, room_manager


@pytest.mark.integration
def test_ping_returns_pong(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
    assert data["type"] == "pong"


@pytest.mark.integration
def test_unknown_event_returns_error(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "unknown_event"})
        data = ws.receive_json()
    assert data["type"] == "error"
    assert "Unknown event type" in data["detail"]


@pytest.mark.integration
def test_invalid_json_returns_error(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_text("not { valid json")
        data = ws.receive_json()
    assert data["type"] == "error"
    assert "Invalid JSON" in data["detail"]


@pytest.mark.integration
def test_join_room_adds_user_to_room_manager(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        # Ping synchronises: pong arrives only after join is processed
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

        assert room_manager.is_member("user_001", "room_1")


@pytest.mark.integration
def test_leave_room_removes_user_from_room_manager(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "leave_room", "room_id": "room_1"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong

        assert not room_manager.is_member("user_001", "room_1")


@pytest.mark.integration
def test_disconnect_cleans_up_room_membership(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "join_room", "room_id": "room_1"})
        ws.send_json({"type": "ping"})
        ws.receive_json()  # pong
    # After context exit the disconnect handler fires
    assert not room_manager.is_member("user_001", "room_1")
    assert connection_manager.get_connection("user_001") is None


@pytest.mark.integration
def test_message_without_room_join_is_silently_dropped(client, valid_token):
    with client.websocket_connect(f"/ws?token={valid_token}") as ws:
        ws.send_json({"type": "message", "room_id": "room_1", "content": "hello"})
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
    # Only the pong comes back — no error for non-member send
    assert data["type"] == "pong"
