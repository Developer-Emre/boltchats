"""
boltchats-storage — Async message persistence worker

Flow:
1. WebSocket sends message → LPUSH to Redis Queue
2. Storage worker BRPOP from queue
3. Persists to MongoDB
4. Publishes event for notifications
"""

import asyncio
import json
from datetime import datetime
import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from aioredis import Redis

logger = structlog.get_logger()


class StorageWorker:
    """
    Consumes messages from Redis queue and persists to MongoDB.
    
    Also handles retries, dead-letter queue, and event publishing.
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        db: AsyncIOMotorDatabase,
        redis: Redis,
        queue_name: str = "messages:queue",
        batch_size: int = 10,
        timeout: int = 5,
    ) -> None:
        self.mongo_client = mongo_client
        self.db = db
        self.redis = redis
        self.queue_name = queue_name
        self.batch_size = batch_size
        self.timeout = timeout
        self.running = False

    async def start(self) -> None:
        """Start the storage worker"""
        self.running = True
        logger.info("storage_worker_started", queue_name=self.queue_name)

        while self.running:
            try:
                await self._process_batch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("storage_worker_error", error=str(e))
                await asyncio.sleep(5)  # Backoff before retry

    async def stop(self) -> None:
        """Stop the storage worker"""
        self.running = False
        logger.info("storage_worker_stopped")

    async def _process_batch(self) -> None:
        """Process a batch of messages from the queue"""
        messages = []

        # Pop up to batch_size messages from queue with timeout
        for _ in range(self.batch_size):
            try:
                # BRPOP with timeout on single message
                result = await asyncio.wait_for(
                    self.redis.brpop(self.queue_name, timeout=self.timeout),
                    timeout=self.timeout + 1,
                )

                if result:
                    queue_name, message_data = result
                    try:
                        message = json.loads(message_data)
                        messages.append(message)
                    except json.JSONDecodeError as e:
                        logger.error(
                            "message_parse_error",
                            error=str(e),
                            raw_data=message_data[:100],
                        )
                        continue
            except asyncio.TimeoutError:
                # No more messages in queue
                break

        if not messages:
            # No messages available, wait before retrying
            await asyncio.sleep(1)
            return

        # Persist batch to MongoDB
        await self._persist_batch(messages)

    async def _persist_batch(self, messages: list[dict]) -> None:
        """
        Persist a batch of messages to MongoDB.
        
        Handles:
        - Duplicate detection (idempotent)
        - Soft deletes
        - Event publishing
        - Dead-letter queue for failures
        """
        saved_count = 0
        failed_messages = []

        for message in messages:
            try:
                await self._persist_message(message)
                saved_count += 1
            except Exception as e:
                logger.error(
                    "message_persist_failed",
                    message_id=message.get("id"),
                    error=str(e),
                )
                failed_messages.append(message)

        # Send failed messages to dead-letter queue
        if failed_messages:
            await self._send_to_dlq(failed_messages)

        logger.info(
            "batch_persisted",
            saved=saved_count,
            failed=len(failed_messages),
            total=len(messages),
        )

    async def _persist_message(self, message: dict) -> None:
        """
        Persist a single message to MongoDB.
        
        Message schema:
        {
            "id": "msg_...",
            "conversation_id": "conv_...",
            "sender_id": "usr_...",
            "content": "Hello",
            "channel": "email|whatsapp|slack",
            "created_at": ISO8601,
            "metadata": {...}
        }
        """
        message_id = message.get("id")
        conversation_id = message.get("conversation_id")

        if not message_id or not conversation_id:
            raise ValueError("message_id and conversation_id are required")

        collection = self.db["messages"]

        # Upsert to ensure idempotency
        result = await collection.update_one(
            {"_id": message_id},
            {
                "$set": {
                    **message,
                    "persisted_at": datetime.utcnow(),
                    "deleted": False,
                }
            },
            upsert=True,
        )

        # Update conversation's last_message_at
        conversations = self.db["conversations"]
        await conversations.update_one(
            {"_id": conversation_id},
            {
                "$set": {"last_message_at": datetime.utcnow()},
                "$inc": {"message_count": 1 if result.upserted_id else 0},
            },
        )

        # Publish event for subscribers
        await self._publish_message_event(message)

        logger.debug(
            "message_persisted",
            message_id=message_id,
            conversation_id=conversation_id,
        )

    async def _publish_message_event(self, message: dict) -> None:
        """Publish message event for downstream subscribers"""
        event = {
            "type": "message.created",
            "message_id": message.get("id"),
            "conversation_id": message.get("conversation_id"),
            "sender_id": message.get("sender_id"),
            "channel": message.get("channel"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        channel = f"room:{message.get('conversation_id')}"
        await self.redis.publish(channel, json.dumps(event))

    async def _send_to_dlq(self, messages: list[dict]) -> None:
        """Send failed messages to dead-letter queue"""
        dlq_name = f"{self.queue_name}:dlq"

        for message in messages:
            message_with_retry = {
                **message,
                "dlq_at": datetime.utcnow().isoformat(),
                "retry_count": message.get("retry_count", 0) + 1,
            }

            await self.redis.lpush(dlq_name, json.dumps(message_with_retry))
            await self.redis.expire(dlq_name, 86400 * 7)  # 7 days retention

        logger.warning(
            "messages_sent_to_dlq",
            dlq=dlq_name,
            count=len(messages),
        )

    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.running:
            await self.stop()
        logger.info("storage_worker_cleanup_complete")
