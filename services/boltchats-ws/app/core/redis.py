import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()

_redis: Redis | None = None


async def connect_redis(url: str) -> None:
    global _redis
    _redis = Redis.from_url(url, decode_responses=True)
    logger.info("redis.connected", url=url)


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("redis.closed")


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis is not connected. Call connect_redis() first.")
    return _redis
