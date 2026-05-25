"""Unit tests for auth_service and core/security — all external deps mocked."""

import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions.http_exceptions import ConflictException, UnauthorizedException
from app.schemas.auth_schema import LoginRequest, RefreshRequest, RegisterRequest
from app.services import auth_service
from app.utils.constants import REDIS_PREFIX_REFRESH_TOKEN


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_collection(
    find_one_return=None, insert_id: ObjectId | None = None
) -> MagicMock:
    ins_result = MagicMock()
    ins_result.inserted_id = insert_id or ObjectId()

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)
    collection.insert_one = AsyncMock(return_value=ins_result)
    return collection


def make_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


# ---------------------------------------------------------------------------
# core/security — unit tests (no I/O)
# ---------------------------------------------------------------------------


def test_hash_and_verify_password() -> None:
    hashed = hash_password("my-secret-pw")
    assert verify_password("my-secret-pw", hashed) is True
    assert verify_password("wrong-pw", hashed) is False


def test_create_access_token_contains_correct_type() -> None:
    token = create_access_token("user42")
    claims = decode_token(token)
    assert claims["sub"] == "user42"
    assert claims["type"] == "access"


def test_create_refresh_token_contains_correct_type() -> None:
    token = create_refresh_token("user42")
    claims = decode_token(token)
    assert claims["sub"] == "user42"
    assert claims["type"] == "refresh"


def test_decode_invalid_token_raises() -> None:
    from jose import JWTError

    with pytest.raises(JWTError):
        decode_token("totally.invalid.token")


# ---------------------------------------------------------------------------
# auth_service.register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success() -> None:
    collection = make_collection(find_one_return=None)
    db = make_db(collection)
    payload = RegisterRequest(
        username="alice", email="alice@example.com", password="securepass1"
    )

    result = await auth_service.register(payload, db)

    assert result.email == "alice@example.com"
    assert result.username == "alice"
    assert result.id
    collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_register_conflict_raises() -> None:
    existing = {"_id": ObjectId(), "email": "alice@example.com"}
    collection = make_collection(find_one_return=existing)
    db = make_db(collection)
    payload = RegisterRequest(
        username="alice", email="alice@example.com", password="securepass1"
    )

    with pytest.raises(ConflictException):
        await auth_service.register(payload, db)


def test_register_request_username_too_short_raises() -> None:
    with pytest.raises(Exception):
        RegisterRequest(username="ab", email="a@b.com", password="securepass1")


def test_register_request_password_too_short_raises() -> None:
    with pytest.raises(Exception):
        RegisterRequest(username="alice", email="a@b.com", password="short")


# ---------------------------------------------------------------------------
# auth_service.login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_success() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    hashed = hash_password("securepass1")
    user_doc = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "hashed_password": hashed,
        "username": "alice",
    }
    collection = make_collection(find_one_return=user_doc)
    db = make_db(collection)
    payload = LoginRequest(email="alice@example.com", password="securepass1")

    result = await auth_service.login(payload, db, redis)

    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"
    await redis.aclose()


@pytest.mark.asyncio
async def test_login_wrong_password_raises() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    hashed = hash_password("securepass1")
    user_doc = {
        "_id": ObjectId(),
        "email": "alice@example.com",
        "hashed_password": hashed,
    }
    collection = make_collection(find_one_return=user_doc)
    db = make_db(collection)
    payload = LoginRequest(email="alice@example.com", password="wrongpassword")

    with pytest.raises(UnauthorizedException):
        await auth_service.login(payload, db, redis)
    await redis.aclose()


@pytest.mark.asyncio
async def test_login_user_not_found_raises() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    collection = make_collection(find_one_return=None)
    db = make_db(collection)
    payload = LoginRequest(email="nobody@example.com", password="securepass1")

    with pytest.raises(UnauthorizedException):
        await auth_service.login(payload, db, redis)
    await redis.aclose()


# ---------------------------------------------------------------------------
# auth_service.refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_success() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    user_id = "user123"
    token = create_refresh_token(user_id)
    await redis.set(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}", token)

    result = await auth_service.refresh(RefreshRequest(refresh_token=token), redis)

    assert result.access_token
    assert result.token_type == "bearer"
    await redis.aclose()


@pytest.mark.asyncio
async def test_refresh_invalid_token_raises() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with pytest.raises(UnauthorizedException):
        await auth_service.refresh(
            RefreshRequest(refresh_token="bad.token.here"), redis
        )
    await redis.aclose()


@pytest.mark.asyncio
async def test_refresh_token_not_in_redis_raises() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    token = create_refresh_token("user123")

    with pytest.raises(UnauthorizedException):
        await auth_service.refresh(RefreshRequest(refresh_token=token), redis)
    await redis.aclose()


@pytest.mark.asyncio
async def test_refresh_with_access_token_raises() -> None:
    """Sending an access token where refresh is expected must fail."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    access = create_access_token("user123")

    with pytest.raises(UnauthorizedException):
        await auth_service.refresh(RefreshRequest(refresh_token=access), redis)
    await redis.aclose()


# ---------------------------------------------------------------------------
# auth_service.logout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_removes_token_from_redis() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    user_id = "user123"
    token = create_refresh_token(user_id)
    await redis.set(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}", token)

    await auth_service.logout(RefreshRequest(refresh_token=token), redis)

    stored = await redis.get(f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}")
    assert stored is None
    await redis.aclose()


@pytest.mark.asyncio
async def test_logout_invalid_token_raises() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    with pytest.raises(UnauthorizedException):
        await auth_service.logout(
            RefreshRequest(refresh_token="bad.token"), redis
        )
    await redis.aclose()
