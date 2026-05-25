import pytest
from unittest.mock import AsyncMock, MagicMock

from app.managers.connection_manager import ConnectionManager


@pytest.fixture
def manager() -> ConnectionManager:
    return ConnectionManager()


@pytest.fixture
def mock_ws() -> MagicMock:
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect_accepts_websocket(manager, mock_ws):
    await manager.connect(mock_ws, "user_1")
    mock_ws.accept.assert_called_once()
    assert manager.get_connection("user_1") is mock_ws


@pytest.mark.asyncio
async def test_connect_increments_active_count(manager, mock_ws):
    assert manager.active_count() == 0
    await manager.connect(mock_ws, "user_1")
    assert manager.active_count() == 1


@pytest.mark.asyncio
async def test_disconnect_removes_connection(manager, mock_ws):
    await manager.connect(mock_ws, "user_1")
    manager.disconnect("user_1")
    assert manager.get_connection("user_1") is None
    assert manager.active_count() == 0


def test_disconnect_unknown_user_is_safe(manager):
    manager.disconnect("nonexistent")  # must not raise


@pytest.mark.asyncio
async def test_send_to_user_delivers_message(manager, mock_ws):
    await manager.connect(mock_ws, "user_1")
    await manager.send_to_user("user_1", "hello")
    mock_ws.send_text.assert_called_once_with("hello")


@pytest.mark.asyncio
async def test_send_to_unknown_user_is_safe(manager):
    await manager.send_to_user("nobody", "hello")  # must not raise


@pytest.mark.asyncio
async def test_send_failure_disconnects_user(manager, mock_ws):
    mock_ws.send_text = AsyncMock(side_effect=RuntimeError("connection lost"))
    await manager.connect(mock_ws, "user_1")
    await manager.send_to_user("user_1", "hello")
    assert manager.get_connection("user_1") is None


@pytest.mark.asyncio
async def test_multiple_users_tracked_independently(manager):
    ws1, ws2 = MagicMock(), MagicMock()
    ws1.accept = ws2.accept = AsyncMock()

    await manager.connect(ws1, "user_1")
    await manager.connect(ws2, "user_2")
    assert manager.active_count() == 2

    manager.disconnect("user_1")
    assert manager.active_count() == 1
    assert manager.get_connection("user_2") is ws2
