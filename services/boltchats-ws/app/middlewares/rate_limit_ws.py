import structlog
from redis.asyncio import Redis

from app.constants.ws_codes import REDIS_PREFIX_RATE_LIMIT_WS

logger = structlog.get_logger()


async def check_message_rate_limit(redis: Redis, user_id: str, limit: int) -> bool:
    """Return True if user is within the per-second message rate limit.

    Uses Redis INCR + EXPIRE with a 1-second sliding window.
    """
    key = f"{REDIS_PREFIX_RATE_LIMIT_WS}{user_id}"
    current: int = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 1)
    within_limit = current <= limit
    if not within_limit:
        logger.warning("rate_limit_ws.exceeded", user_id=user_id, count=current)
    return within_limit
