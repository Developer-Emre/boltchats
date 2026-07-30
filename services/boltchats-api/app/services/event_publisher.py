"""
Event Publisher

Publish domain events to Redis queue and MongoDB event store
"""

import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import DomainEvent, EventType, EventStatus
from app.repositories import DomainEventRepository
from app.utils.sparkquark_constants import RedisKeys

from .base import BaseService


class EventPublisher(BaseService):
    """Publish domain events to queue and event store"""

    def __init__(self, db: AsyncIOMotorDatabase, redis_client: redis.Redis):
        super().__init__(db)
        self.events = DomainEventRepository(db)
        self.redis = redis_client

    async def publish_event(
        self,
        event_type: EventType,
        org_id: str,
        aggregate_id: str,
        aggregate_type: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Publish event to both MongoDB (event store) and Redis queue.
        
        This implements Write-Behind pattern:
        1. Save to MongoDB immediately (event store)
        2. Queue in Redis for async processors
        3. Return event_id synchronously
        
        Args:
            event_type: Type of domain event
            org_id: Organization ID (multi-tenant)
            aggregate_id: ID of affected resource (customer_id, conversation_id, etc)
            aggregate_type: Resource type (customer, conversation, message, etc)
            data: Event payload
            metadata: Additional context (user_id, source, etc)
        
        Returns:
            event_id: ID of stored event
        """
        # Create event
        event = DomainEvent(
            event_type=event_type,
            organization_id=org_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=data,
            metadata=metadata or {},
            status=EventStatus.PENDING,
        )

        # Save to MongoDB
        event_id = await self.events.create(event)

        # Queue in Redis
        queue_key = RedisKeys.EVENT_QUEUE
        event_payload = {
            "event_id": event_id,
            "event_type": event_type,
            "org_id": org_id,
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
            "data": data,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.redis.lpush(
            queue_key,
            json.dumps(event_payload, default=str),
        )

        self.logger.info(
            "event_published",
            event_type=event_type,
            event_id=event_id,
            aggregate_id=aggregate_id,
        )

        return event_id

    async def mark_event_processed(self, event_id: str) -> None:
        """Mark event as processed in event store."""
        await self.events.update(event_id, {
            "status": EventStatus.PROCESSED,
            "processed_at": datetime.now(timezone.utc),
        })

    async def mark_event_failed(self, event_id: str, error: str) -> None:
        """Mark event as failed in event store."""
        await self.events.update(event_id, {
            "status": EventStatus.FAILED,
            "failed_at": datetime.now(timezone.utc),
            "error_message": error,
        })

    async def get_pending_events(
        self,
        org_id: str,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Get pending events for processing."""
        events = await self.events.find({
            "organization_id": org_id,
            "status": EventStatus.PENDING,
        })
        return events[:limit]

    async def get_event_history(
        self,
        org_id: str,
        aggregate_id: str,
        limit: int = 50,
    ) -> list[DomainEvent]:
        """Get event history for a resource (audit trail)."""
        events = await self.events.find({
            "organization_id": org_id,
            "aggregate_id": aggregate_id,
        })
        return events[:limit]

    async def replay_events(
        self,
        org_id: str,
        aggregate_id: str,
    ) -> list[DomainEvent]:
        """
        Replay all events for an aggregate to rebuild state.
        
        Useful for:
        - Rebuilding conversation state from events
        - Debugging
        - Testing
        """
        return await self.get_event_history(org_id, aggregate_id, limit=10000)


class EventSubscriber:
    """Subscribe to events from Redis queue"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def subscribe_events(self, callback) -> None:
        """
        Subscribe to events from queue.
        
        Callback receives event payload dict.
        Must handle exceptions gracefully.
        """
        queue_key = RedisKeys.EVENT_QUEUE
        
        while True:
            try:
                # BRPOP blocks until item available (0 = infinite timeout)
                result = await self.redis.brpop(queue_key, timeout=1)
                
                if result:
                    _, event_json = result
                    event_data = json.loads(event_json)
                    
                    try:
                        await callback(event_data)
                    except Exception as e:
                        # Log error but continue processing
                        print(f"Event callback error: {e}")
                        # Re-queue failed event or log to DLQ
                        
            except Exception as e:
                # Connection error
                print(f"Event subscription error: {e}")
                await asyncio.sleep(1)  # Backoff


# Concrete event types
async def publish_message_received_event(
    publisher: EventPublisher,
    org_id: str,
    conv_id: str,
    msg_id: str,
    member_id: str,
    content: str,
) -> str:
    """Publish when message received"""
    return await publisher.publish_event(
        EventType.MESSAGE_RECEIVED,
        org_id=org_id,
        aggregate_id=conv_id,
        aggregate_type="conversation",
        data={
            "message_id": msg_id,
            "content": content[:100],  # Preview
        },
        metadata={"member_id": member_id},
    )


async def publish_conversation_assigned_event(
    publisher: EventPublisher,
    org_id: str,
    conv_id: str,
    member_id: str,
) -> str:
    """Publish when conversation assigned"""
    return await publisher.publish_event(
        EventType.CONVERSATION_ASSIGNED,
        org_id=org_id,
        aggregate_id=conv_id,
        aggregate_type="conversation",
        data={"assigned_to": member_id},
        metadata={"member_id": member_id},
    )


async def publish_conversation_closed_event(
    publisher: EventPublisher,
    org_id: str,
    conv_id: str,
) -> str:
    """Publish when conversation closed"""
    return await publisher.publish_event(
        EventType.CONVERSATION_CLOSED,
        org_id=org_id,
        aggregate_id=conv_id,
        aggregate_type="conversation",
        data={},
    )


async def publish_customer_created_event(
    publisher: EventPublisher,
    org_id: str,
    customer_id: str,
    name: str,
) -> str:
    """Publish when customer created"""
    return await publisher.publish_event(
        EventType.CUSTOMER_CREATED,
        org_id=org_id,
        aggregate_id=customer_id,
        aggregate_type="customer",
        data={"name": name},
    )


async def publish_integration_connected_event(
    publisher: EventPublisher,
    org_id: str,
    integration_id: str,
    provider: str,
) -> str:
    """Publish when integration connected"""
    return await publisher.publish_event(
        EventType.INTEGRATION_CONNECTED,
        org_id=org_id,
        aggregate_id=integration_id,
        aggregate_type="integration",
        data={"provider": provider},
    )
