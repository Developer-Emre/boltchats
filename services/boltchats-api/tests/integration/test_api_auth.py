"""Integration tests — HTTP layer via ASGI client, mocked DB + Redis."""

import pytest
import pytest_asyncio
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient

from app.core.database import get_database
from app.core.redis import get_redis
from app.core.security import create_refresh_token, hash_password
from app.main import app
from app.utils.constants import REDIS_PREFIX_REFRESH_TOKEN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_collection(find_one_return=None) -> MagicMock:
    ins_result = MagicMock()
    ins_result.inserted_id = ObjectId()
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)
    collection.insert_one = AsyncMock(return_value=ins_result)
    return collection


@pytest_asyncio.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def api_client(redis):
    collection = _make_collection(find_one_return=None)
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_redis] = lambda: redis
    app.state.redis = redis  # used by RateLimitMiddleware

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, db, collection
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "boltchats-api"}


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_returns_201(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "securepass1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "alice"
    assert "id" in body


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_conflict_returns_409(api_client) -> None:
    ac, db, _ = api_client
    existing = {"_id": ObjectId(), "email": "alice@example.com"}
    conflict_collection = _make_collection(find_one_return=existing)
    db.__getitem__ = MagicMock(return_value=conflict_collection)

    response = await ac.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "securepass1"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_invalid_email_returns_422(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.post(
        "/auth/register",
        json={"username": "alice", "email": "not-an-email", "password": "securepass1"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_success_returns_tokens(api_client) -> None:
    ac, db, _ = api_client
    hashed = hash_password("securepass1")
    user_doc = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "hashed_password": hashed,
        "username": "alice",
    }
    login_collection = _make_collection(find_one_return=user_doc)
    db.__getitem__ = MagicMock(return_value=login_collection)

    response = await ac.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "securepass1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_wrong_password_returns_401(api_client) -> None:
    ac, db, _ = api_client
    hashed = hash_password("securepass1")
    user_doc = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "hashed_password": hashed,
    }
    login_collection = _make_collection(find_one_return=user_doc)
    db.__getitem__ = MagicMock(return_value=login_collection)

    response = await ac.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_unknown_user_returns_401(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "securepass1"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_returns_new_access_token(api_client, redis) -> None:
    ac, _, _ = api_client
    user_id = "user_abc"
    token = create_refresh_token(user_id)
    await redis.set(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}", token)

    response = await ac.post("/auth/refresh", json={"refresh_token": token})

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_bad_token_returns_401(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.post("/auth/refresh", json={"refresh_token": "bad.token"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout_returns_204(api_client, redis) -> None:
    ac, _, _ = api_client
    user_id = "user_abc"
    token = create_refresh_token(user_id)
    await redis.set(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}", token)

    response = await ac.post("/auth/logout", json={"refresh_token": token})

    assert response.status_code == 204
    stored = await redis.get(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}")
    assert stored is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout_bad_token_returns_401(api_client) -> None:
    ac, _, _ = api_client
    response = await ac.post("/auth/logout", json={"refresh_token": "bad.token"})
    assert response.status_code == 401
