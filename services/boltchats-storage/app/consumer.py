import json
from datetime import datetime, timezone

import structlog
from redis.asyncio import Redis

from app.core.config import settings
from app.storage import MessageRepository
from app.utils.metrics import record_consumed

logger = structlog.get_logger()


async def consume(redis: Redis, repo: MessageRepository) -> None:
    """BRPOP loop — blocks until a message arrives, then persists it to MongoDB.

    BRPOP is used ONLY here. Never use SUBSCRIBE in this service.
    """
    logger.info("consumer.started", queue=settings.redis_queue_name)

    while True:
        raw = await redis.brpop(settings.redis_queue_name, timeout=0)
        if raw is None:
            continue

        _, message_json = raw

        try:
            payload: dict = json.loads(message_json)
            # Ensure created_at is stored as a datetime object
            if "created_at" in payload and isinstance(payload["created_at"], str):
                payload["created_at"] = datetime.fromisoformat(payload["created_at"])
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("consumer.parse_failed", error=str(exc), raw=message_json)
            continue

        try:
            await repo.insert(payload)
            record_consumed()
            logger.info(
                "consumer.message_persisted",
                room_id=payload.get("room_id"),
                sender_id=payload.get("sender_id"),
            )
        except RuntimeError:
            # Already logged with full detail inside MessageRepository
            pass
