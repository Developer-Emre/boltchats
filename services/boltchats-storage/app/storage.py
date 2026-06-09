import asyncio

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.utils.constants import MESSAGES_COLLECTION
from app.utils.metrics import record_failed

logger = structlog.get_logger()


class MessageRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[MESSAGES_COLLECTION]

    async def insert(self, payload: dict) -> str:
        """Insert a message document with exponential backoff on failure.
        
        Returns the MongoDB ObjectId (_id) of the inserted document.
        """
        delay = settings.consumer_retry_base_delay
        last_exc: Exception | None = None

        for attempt in range(1, settings.consumer_max_retries + 1):
            try:
                result = await self._collection.insert_one(payload)
                inserted_id = str(result.inserted_id)
                logger.debug(
                    "storage.inserted",
                    room_id=payload.get("room_id"),
                    sender_id=payload.get("sender_id"),
                    attempt=attempt,
                    message_id=inserted_id,
                )
                return inserted_id
            except PyMongoError as exc:
                last_exc = exc
                record_failed()
                logger.warning(
                    "storage.insert_failed",
                    attempt=attempt,
                    max_retries=settings.consumer_max_retries,
                    error=str(exc),
                )
                if attempt < settings.consumer_max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2

        logger.error(
            "storage.insert_exhausted",
            max_retries=settings.consumer_max_retries,
            error=str(last_exc),
        )
        raise RuntimeError("MongoDB insert failed after retries") from last_exc
