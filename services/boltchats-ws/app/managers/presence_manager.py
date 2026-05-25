import structlog
from redis.asyncio import Redis

from app.constants.ws_codes import REDIS_KEY_PRESENCE_ONLINE, REDIS_PREFIX_PRESENCE_ROOM

logger = structlog.get_logger()


class PresenceManager:
    """Online user tracking via Redis Sets.

    Keys written here are read (read-only) by boltchats-api's presence endpoints.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def user_online(self, user_id: str, room_id: str) -> None:
        """Mark user as online globally and in the given room."""
        await self._redis.sadd(f"{REDIS_PREFIX_PRESENCE_ROOM}{room_id}", user_id)
        await self._redis.sadd(REDIS_KEY_PRESENCE_ONLINE, user_id)
        logger.info("presence.online", user_id=user_id, room_id=room_id)

    async def user_offline_room(self, user_id: str, room_id: str) -> None:
        """Remove user from a specific room's presence set."""
        await self._redis.srem(f"{REDIS_PREFIX_PRESENCE_ROOM}{room_id}", user_id)
        logger.info("presence.left_room", user_id=user_id, room_id=room_id)

    async def user_offline(self, user_id: str, room_ids: list[str]) -> None:
        """Remove user from all room presence sets and the global online set."""
        for room_id in room_ids:
            await self._redis.srem(f"{REDIS_PREFIX_PRESENCE_ROOM}{room_id}", user_id)
        await self._redis.srem(REDIS_KEY_PRESENCE_ONLINE, user_id)
        logger.info("presence.offline", user_id=user_id, rooms=room_ids)
