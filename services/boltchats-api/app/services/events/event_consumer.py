"""
Event Consumer

Async worker that consumes events from Redis queue and processes them.
Runs in background, polling Redis BRPOP for new events.
"""

import asyncio
from typing import Optional

import redis.asyncio as redis
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import DomainEvent, EventStatus
from app.repositories import EventRepository
from app.services.base import BaseService
from app.utils.sparkquark_constants import RedisKey


logger = structlog.get_logger()


class EventConsumer(BaseService):
    """
    Event consumer for async event processing.
    
    Polls Redis queue for events, processes them, and marks as complete.
    Can retry failed events up to max retries.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
        event_bus,  # EventBus instance
        batch_size: int = 10,
        poll_timeout: int = 5,
        max_retries: int = 3,
    ):
        super().__init__(db)
        self.events = EventRepository(db)
        self.redis = redis_client
        self.event_bus = event_bus
        self.batch_size = batch_size
        self.poll_timeout = poll_timeout
        self.max_retries = max_retries
        self.running = False

    async def start(self) -> None:
        """Start consuming events."""
        logger.info("event_consumer_starting")
        self.running = True

        try:
            while self.running:
                await self._process_batch()
        except asyncio.CancelledError:
            logger.info("event_consumer_cancelled")
        except Exception as e:
            logger.error("event_consumer_error", error=str(e))
            raise

    async def stop(self) -> None:
        """Stop consuming events gracefully."""
        logger.info("event_consumer_stopping")
        self.running = False

    async def _process_batch(self) -> None:
        """Process batch of events from queue."""
        queue_key = RedisKey.MESSAGE_QUEUE.value.format(
            queue="event_queue"
        )

        for _ in range(self.batch_size):
            try:
                # BRPOP: blocking right pop (consumes from right, highest priority)
                result = await asyncio.wait_for(
                    self.redis.brpop(queue_key, timeout=self.poll_timeout),
                    timeout=self.poll_timeout + 1,
                )

                if not result:
                    continue

                _, event_id = result
                event_id = event_id.decode() if isinstance(event_id, bytes) else event_id

                await self._process_event(event_id)

            except asyncio.TimeoutError:
                # No events in queue, continue
                break
            except Exception as e:
                logger.error(
                    "batch_processing_error",
                    error=str(e),
                )

    async def _process_event(self, event_id: str) -> None:
        """
        Process single event.
        
        Args:
            event_id: Event ID from queue
        """
        event = await self.events.read(event_id)
        if not event:
            logger.warning(
                "event_not_found",
                event_id=event_id,
            )
            return

        if event.status == EventStatus.PROCESSED:
            logger.debug(
                "event_already_processed",
                event_id=event_id,
            )
            return

        retry_count = event.retry_count or 0

        try:
            # Call event bus handlers
            await self.event_bus.handle_event(event)

            # Mark as processed
            await self.events.update(event_id, {
                "status": EventStatus.PROCESSED,
            })

            logger.info(
                "event_processed",
                event_id=event_id,
                event_type=event.event_type,
            )

        except Exception as e:
            logger.error(
                "event_processing_failed",
                event_id=event_id,
                event_type=event.event_type,
                retry_count=retry_count,
                error=str(e),
            )

            if retry_count < self.max_retries:
                # Re-queue for retry
                queue_key = RedisKey.MESSAGE_QUEUE.value.format(
                    queue="event_queue"
                )
                await self.redis.lpush(queue_key, event_id)
                await self.events.update(event_id, {
                    "retry_count": retry_count + 1,
                    "status": EventStatus.PENDING,
                })
            else:
                # Max retries exceeded, mark as failed
                await self.events.update(event_id, {
                    "status": EventStatus.FAILED,
                    "error_message": str(e),
                })

                logger.error(
                    "event_max_retries_exceeded",
                    event_id=event_id,
                    event_type=event.event_type,
                )

    async def get_pending_events(self, org_id: str) -> list[DomainEvent]:
        """Get pending events for organization."""
        return await self.events.find({
            "organization_id": org_id,
            "status": EventStatus.PENDING,
        })

    async def get_failed_events(self, org_id: str) -> list[DomainEvent]:
        """Get failed events for organization."""
        return await self.events.find({
            "organization_id": org_id,
            "status": EventStatus.FAILED,
        })

    async def retry_failed_event(self, event_id: str) -> bool:
        """Manually retry a failed event."""
        event = await self.events.read(event_id)
        if not event:
            return False

        queue_key = RedisKey.MESSAGE_QUEUE.value.format(
            queue="event_queue"
        )
        await self.redis.lpush(queue_key, event_id)
        await self.events.update(event_id, {
            "retry_count": 0,
            "status": EventStatus.PENDING,
        })

        logger.info(
            "event_retry_manual",
            event_id=event_id,
        )

        return True

    async def get_stats(self) -> dict:
        """Get consumer stats."""
        queue_key = RedisKey.MESSAGE_QUEUE.value.format(
            queue="event_queue"
        )
        queue_length = await self.redis.llen(queue_key)

        return {
            "running": self.running,
            "queue_length": queue_length,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
        }
