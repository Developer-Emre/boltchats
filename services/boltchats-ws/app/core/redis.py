import structlog
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

logger = structlog.get_logger()

_redis: Redis | None = None


async def connect_redis(url: str) -> None:
    global _redis
    # Create connection pool with NO socket timeout (None = blocking forever)
    # This prevents pub/sub listening from timing out on idle
    connection_pool = ConnectionPool.from_url(
        url,
        decode_responses=True,
        socket_keepalive=True,
        socket_timeout=None,
        health_check_interval=30,
        max_connections=20
    )
    _redis = Redis(connection_pool=connection_pool)
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
