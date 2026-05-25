import fakeredis
import fakeredis.aioredis
import pytest
from jose import jwt
from starlette.testclient import TestClient
from unittest.mock import AsyncMock, patch

import app.core.redis as redis_module
import app.main as main_module
from app.core.config import get_settings
from app.main import app, connection_manager, room_manager

settings = get_settings()


def make_token(user_id: str = "user_001") -> str:
    return jwt.encode(
        {"sub": user_id}, settings.secret_key, algorithm=settings.algorithm
    )


@pytest.fixture
def fake_server() -> fakeredis.FakeServer:
    """Isolated FakeServer per test — prevents cross-test state bleed."""
    return fakeredis.FakeServer()


@pytest.fixture
def fake_redis(fake_server: fakeredis.FakeServer) -> fakeredis.aioredis.FakeRedis:
    """Async FakeRedis backed by the per-test FakeServer."""
    return fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)


@pytest.fixture
def sync_redis(fake_server: fakeredis.FakeServer) -> fakeredis.FakeRedis:
    """Sync FakeRedis sharing the same FakeServer — safe for assertion reads."""
    return fakeredis.FakeRedis(server=fake_server, decode_responses=True)


@pytest.fixture(autouse=True)
def reset_state():
    """Clear in-memory singletons between tests."""
    connection_manager._connections.clear()
    room_manager._room_members.clear()
    room_manager._user_rooms.clear()
    yield
    connection_manager._connections.clear()
    room_manager._room_members.clear()
    room_manager._user_rooms.clear()


@pytest.fixture
def client(fake_redis, monkeypatch):
    """TestClient with fake Redis and patched broadcast subscriber loop.

    connect_redis and close_redis are patched on app.main (the imported name)
    rather than on app.core.redis, because main.py binds them at import time
    via `from app.core.redis import connect_redis, close_redis`.
    """
    # Set fake Redis as the module-level singleton BEFORE lifespan runs
    monkeypatch.setattr(redis_module, "_redis", fake_redis)

    async def noop_connect(url: str) -> None:
        pass  # Prevents real connect from overwriting _redis with a real client

    async def noop_close() -> None:
        pass

    monkeypatch.setattr(main_module, "connect_redis", noop_connect)
    monkeypatch.setattr(main_module, "close_redis", noop_close)

    with (
        patch(
            "app.managers.broadcast_manager.BroadcastManager.start",
            new_callable=AsyncMock,
        ),
        patch(
            "app.managers.broadcast_manager.BroadcastManager.stop",
            new_callable=AsyncMock,
        ),
    ):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def valid_token() -> str:
    return make_token()


@pytest.fixture
def valid_token_user2() -> str:
    return make_token("user_002")
