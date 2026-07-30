"""
Event Bus

Central event dispatcher for async event processing.
Events are persisted to MongoDB and queued in Redis for async processing.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Optional

import redis.asyncio as redis
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import DomainEvent, EventStatus, EventType
from app.repositories import EventRepository
from app.services.base import BaseService
from app.utils.sparkquark_constants import Collection, RedisKey


logger = structlog.get_logger()


class EventSubscription:
    """Event subscription handler"""

    def __init__(
        self,
        event_type: EventType,
        handler: Callable,
        priority: int = 0,
    ):
        self.event_type = event_type
        self.handler = handler
        self.priority = priority


class EventBus(BaseService):
    """
    Event bus for publishing and consuming domain events.
    
    Pattern:
    1. Service publishes event → EventBus.publish()
    2. EventBus saves to MongoDB + Redis queue
    3. Async consumer processes event → calls subscribed handlers
    4. Handlers update state → may publish more events
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
    ):
        super().__init__(db)
        self.events = EventRepository(db)
        self.redis = redis_client
        self._subscriptions: dict[str, list[EventSubscription]] = {}

    async def publish(
        self,
        org_id: str,
        event_type: EventType,
        aggregate_id: str,
        aggregate_type: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ) -> str:
        """
        Publish domain event.
        
        Event is saved to MongoDB + queued in Redis for async processing.
        
        Args:
            org_id: Organization ID (multi-tenant)
            event_type: Event type (MessageSent, ConversationAssigned, etc)
            aggregate_id: ID of aggregate (message_id, conversation_id, etc)
            aggregate_type: Type of aggregate (Message, Conversation, etc)
            data: Event payload
            correlation_id: Trace ID for related events
            causation_id: ID of event that caused this
            
        Returns:
            Event ID
        """
        event = DomainEvent(
            organization_id=org_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            data=data,
            correlation_id=correlation_id,
            causation_id=causation_id,
            status=EventStatus.PUBLISHED,
            created_at=datetime.now(timezone.utc),
        )

        # Save event (event sourcing)
        event_id = await self.events.create(event)

        # Queue event for async processing
        queue_key = RedisKey.MESSAGE_QUEUE.value.format(
            queue="event_queue"
        )
        await self.redis.lpush(queue_key, event_id)

        logger.info(
            "event_published",
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            organization_id=org_id,
        )

        await self.log_action(
            "event_published",
            resource_id=event_id,
            resource_type="event",
            details={
                "event_type": event_type,
                "aggregate_id": aggregate_id,
            },
        )

        return event_id

    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        priority: int = 0,
    ) -> None:
        """
        Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to
            handler: Async handler function (event: DomainEvent) -> None
            priority: Handler priority (higher = earlier execution)
        """
        key = event_type
        if key not in self._subscriptions:
            self._subscriptions[key] = []

        subscription = EventSubscription(event_type, handler, priority)
        self._subscriptions[key].append(subscription)

        # Sort by priority (descending)
        self._subscriptions[key].sort(
            key=lambda s: s.priority,
            reverse=True,
        )

        logger.info(
            "event_subscribed",
            event_type=event_type,
            handler=handler.__name__,
            priority=priority,
        )

    async def unsubscribe(
        self,
        event_type: EventType,
        handler: Callable,
    ) -> None:
        """Unsubscribe from event type."""
        key = event_type
        if key not in self._subscriptions:
            return

        self._subscriptions[key] = [
            s for s in self._subscriptions[key]
            if s.handler != handler
        ]

        logger.info(
            "event_unsubscribed",
            event_type=event_type,
            handler=handler.__name__,
        )

    async def handle_event(self, event: DomainEvent) -> None:
        """
        Handle event by calling all subscribed handlers.
        
        Args:
            event: Event to handle
        """
        key = event.event_type
        handlers = self._subscriptions.get(key, [])

        if not handlers:
            logger.warning(
                "no_handlers_for_event",
                event_type=event.event_type,
                event_id=event.id,
            )
            return

        for subscription in handlers:
            try:
                await subscription.handler(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_id=event.id,
                    event_type=event.event_type,
                    handler=subscription.handler.__name__,
                    error=str(e),
                )
                # Continue to next handler on error
                raise

    async def replay_events(
        self,
        org_id: str,
        aggregate_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
    ) -> int:
        """
        Replay events for event sourcing.
        
        Useful for:
        - Rebuilding read models
        - Testing event handlers
        - Auditing event history
        
        Args:
            org_id: Organization ID
            aggregate_id: Optional filter by aggregate
            event_type: Optional filter by event type
            
        Returns:
            Number of events replayed
        """
        query = {"organization_id": org_id}
        if aggregate_id:
            query["aggregate_id"] = aggregate_id
        if event_type:
            query["event_type"] = event_type

        events = await self.events.find(query)
        count = 0

        for event in events:
            try:
                await self.handle_event(event)
                count += 1
            except Exception as e:
                logger.error(
                    "replay_failed",
                    event_id=event.id,
                    error=str(e),
                )

        logger.info(
            "events_replayed",
            count=count,
            organization_id=org_id,
        )

        return count

    async def get_events(
        self,
        org_id: str,
        aggregate_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[DomainEvent]:
        """Get events for aggregate or organization."""
        query = {"organization_id": org_id}
        if aggregate_id:
            query["aggregate_id"] = aggregate_id

        return await self.events.find(query, limit=limit)

    def get_subscriptions(self, event_type: Optional[EventType] = None) -> dict:
        """Get current subscriptions."""
        if event_type:
            return {
                event_type: [
                    {
                        "handler": s.handler.__name__,
                        "priority": s.priority,
                    }
                    for s in self._subscriptions.get(event_type, [])
                ]
            }

        return {
            event_type: [
                {
                    "handler": s.handler.__name__,
                    "priority": s.priority,
                }
                for s in handlers
            ]
            for event_type, handlers in self._subscriptions.items()
        }
