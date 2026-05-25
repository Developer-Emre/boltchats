import structlog
from redis.asyncio import Redis

from app.schemas.presence_schema import (
    OnlineUsersResponse,
    RoomPresenceResponse,
    UserPresenceResponse,
)
from app.utils.constants import REDIS_KEY_PRESENCE_ONLINE, REDIS_PREFIX_PRESENCE_ROOM

logger = structlog.get_logger()


async def get_room_presence(room_id: str, redis: Redis) -> RoomPresenceResponse:
    """Return the set of user_ids currently online in a given room."""
    key = f"{REDIS_PREFIX_PRESENCE_ROOM}{room_id}"
    members: set[str] = await redis.smembers(key)
    user_ids = sorted(members)  # deterministic order for tests / caching
    return RoomPresenceResponse(
        room_id=room_id,
        online_user_ids=user_ids,
        count=len(user_ids),
    )


async def get_user_presence(user_id: str, redis: Redis) -> UserPresenceResponse:
    """Return whether a specific user is currently online (globally)."""
    is_online: bool = bool(
        await redis.sismember(REDIS_KEY_PRESENCE_ONLINE, user_id)
    )
    return UserPresenceResponse(user_id=user_id, is_online=is_online)


async def get_online_users(redis: Redis) -> OnlineUsersResponse:
    """Return the full set of globally online user_ids."""
    members: set[str] = await redis.smembers(REDIS_KEY_PRESENCE_ONLINE)
    user_ids = sorted(members)
    return OnlineUsersResponse(online_user_ids=user_ids, count=len(user_ids))
