import structlog
from redis.asyncio import Redis

from app.constants.ws_codes import REDIS_QUEUE_MESSAGES

logger = structlog.get_logger()


class MessageQueue:
    """Write-Behind queue for message persistence.

    LPUSH only — never use PUBLISH here.
    boltchats-storage consumes messages from this queue via BRPOP.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def enqueue(self, message_json: str) -> None:
        """Push a serialised QueueMessage JSON string to the persistence queue."""
        await self._redis.lpush(REDIS_QUEUE_MESSAGES, message_json)
        logger.debug("message_queue.enqueued")
