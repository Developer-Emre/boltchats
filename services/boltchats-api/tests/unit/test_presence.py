"""Unit tests for presence_service — only fakeredis, no HTTP layer."""

import pytest
import fakeredis.aioredis

from app.services import presence_service
from app.utils.constants import REDIS_KEY_PRESENCE_ONLINE, REDIS_PREFIX_PRESENCE_ROOM


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOM_ID = "room_abc"
USER_A = "user_001"
USER_B = "user_002"
USER_C = "user_003"


async def _seed_room(redis, room_id: str, *user_ids: str) -> None:
    key = f"{REDIS_PREFIX_PRESENCE_ROOM}{room_id}"
    for uid in user_ids:
        await redis.sadd(key, uid)


async def _seed_online(redis, *user_ids: str) -> None:
    for uid in user_ids:
        await redis.sadd(REDIS_KEY_PRESENCE_ONLINE, uid)


# ---------------------------------------------------------------------------
# get_room_presence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_room_presence_with_members() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_room(redis, ROOM_ID, USER_A, USER_B)

    result = await presence_service.get_room_presence(ROOM_ID, redis)

    assert result.room_id == ROOM_ID
    assert set(result.online_user_ids) == {USER_A, USER_B}
    assert result.count == 2
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_room_presence_empty_room() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    result = await presence_service.get_room_presence(ROOM_ID, redis)

    assert result.room_id == ROOM_ID
    assert result.online_user_ids == []
    assert result.count == 0
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_room_presence_isolated_per_room() -> None:
    """Members of room_1 must not appear in room_2 results."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_room(redis, "room_1", USER_A)
    await _seed_room(redis, "room_2", USER_B)

    r1 = await presence_service.get_room_presence("room_1", redis)
    r2 = await presence_service.get_room_presence("room_2", redis)

    assert set(r1.online_user_ids) == {USER_A}
    assert set(r2.online_user_ids) == {USER_B}
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_room_presence_count_matches_list() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_room(redis, ROOM_ID, USER_A, USER_B, USER_C)

    result = await presence_service.get_room_presence(ROOM_ID, redis)

    assert result.count == len(result.online_user_ids)
    await redis.aclose()


# ---------------------------------------------------------------------------
# get_user_presence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_presence_online() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_online(redis, USER_A)

    result = await presence_service.get_user_presence(USER_A, redis)

    assert result.user_id == USER_A
    assert result.is_online is True
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_user_presence_offline() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    result = await presence_service.get_user_presence(USER_A, redis)

    assert result.user_id == USER_A
    assert result.is_online is False
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_user_presence_only_checks_target_user() -> None:
    """USER_B online must not affect USER_A's presence check."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_online(redis, USER_B)

    result = await presence_service.get_user_presence(USER_A, redis)

    assert result.is_online is False
    await redis.aclose()


# ---------------------------------------------------------------------------
# get_online_users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_online_users_returns_all() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_online(redis, USER_A, USER_B, USER_C)

    result = await presence_service.get_online_users(redis)

    assert set(result.online_user_ids) == {USER_A, USER_B, USER_C}
    assert result.count == 3
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_online_users_empty() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    result = await presence_service.get_online_users(redis)

    assert result.online_user_ids == []
    assert result.count == 0
    await redis.aclose()


@pytest.mark.asyncio
async def test_get_online_users_count_matches_list() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    await _seed_online(redis, USER_A, USER_B)

    result = await presence_service.get_online_users(redis)

    assert result.count == len(result.online_user_ids)
    await redis.aclose()
