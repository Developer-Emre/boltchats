import json
from datetime import datetime, timezone

import structlog
from redis.asyncio import Redis

from app.core.config import settings
from app.storage import MessageRepository
from app.utils.metrics import record_consumed

logger = structlog.get_logger()

# Redis Pub/Sub channel for message confirmations
REDIS_CHANNEL_MESSAGE_CONFIRMED = "message:confirmed"


async def consume(redis: Redis, repo: MessageRepository) -> None:
    """BRPOP loop — blocks until a message arrives, then persists it to MongoDB.

    After successful persistence, publishes confirmation event via Redis Pub/Sub
    so WS service can notify the client with the MongoDB ObjectId.

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
            mongodb_oid = await repo.insert(payload)
            record_consumed()
            
            # Publish confirmation with ObjectId to WS service
            confirmation = {
                "client_message_id": payload.get("id"),
                "server_id": mongodb_oid,
                "room_id": payload.get("room_id"),
            }
            await redis.publish(
                REDIS_CHANNEL_MESSAGE_CONFIRMED,
                json.dumps(confirmation),
            )
            
            logger.info(
                "consumer.message_persisted",
                room_id=payload.get("room_id"),
                sender_id=payload.get("sender_id"),
                mongodb_id=mongodb_oid,
            )
        except RuntimeError:
            # Already logged with full detail inside MessageRepository
            pass
