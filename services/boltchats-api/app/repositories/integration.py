"""
Integration Domain Repositories

Integrations, Events, Audit Logs, Notifications
"""

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import (
    AuditLog,
    DomainEvent,
    Integration,
    Notification,
)
from app.utils.sparkquark_constants import Collection

from .base import BaseRepository


class IntegrationRepository(BaseRepository[Integration]):
    """Repository for provider integrations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.INTEGRATIONS.value, Integration)

    async def find_by_org(self, organization_id: str) -> list[Integration]:
        """Find all integrations in organization"""
        return await self.find_many({"organization_id": organization_id})

    async def find_by_provider(self, organization_id: str, provider: str) -> list[Integration]:
        """Find all integrations for a provider"""
        return await self.find_many({
            "organization_id": organization_id,
            "provider": provider
        })

    async def find_connected(self, organization_id: str) -> list[Integration]:
        """Find all connected integrations"""
        return await self.find_many({
            "organization_id": organization_id,
            "status": "connected"
        })

    async def find_by_account(self, organization_id: str, provider: str, provider_account_id: str) -> Integration | None:
        """Find integration by provider account"""
        return await self.find({
            "organization_id": organization_id,
            "provider": provider,
            "provider_account_id": provider_account_id
        })


class DomainEventRepository(BaseRepository[DomainEvent]):
    """Repository for domain events (event sourcing)"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.EVENTS.value, DomainEvent)

    async def find_by_org(
        self, organization_id: str, skip: int = 0, limit: int = 100
    ) -> list[DomainEvent]:
        """Find events in organization (reverse chronological)"""
        cursor = self.collection.find({"organization_id": organization_id})
        cursor.sort("created_at", -1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model_class.model_validate(doc) for doc in docs]

    async def find_by_entity(self, organization_id: str, entity_id: str) -> list[DomainEvent]:
        """Find all events for an entity"""
        return await self.find_many({
            "organization_id": organization_id,
            "entity_id": entity_id
        })

    async def find_by_type(self, organization_id: str, event_type: str) -> list[DomainEvent]:
        """Find events by type"""
        return await self.find_many({
            "organization_id": organization_id,
            "event_type": event_type
        })

    async def find_by_actor(self, organization_id: str, actor_id: str) -> list[DomainEvent]:
        """Find events triggered by actor"""
        return await self.find_many({
            "organization_id": organization_id,
            "actor_id": actor_id
        })

    async def get_event_chain(self, event_id: str) -> list[DomainEvent]:
        """Get chain of related events (for causality tracking)"""
        event = await self.read(event_id)
        if not event:
            return []
        
        # Find all events in chain
        chain = [event]
        current = event
        
        # Follow caused_by links
        while current.caused_by:
            caused_by_event = await self.read(current.caused_by)
            if caused_by_event:
                chain.insert(0, caused_by_event)
                current = caused_by_event
            else:
                break
        
        return chain


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit logs (compliance)"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.AUDIT_LOGS.value, AuditLog)

    async def find_by_org(
        self, organization_id: str, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        """Find audit logs in organization"""
        return await self.find_many(
            {"organization_id": organization_id},
            skip=skip,
            limit=limit
        )

    async def find_by_actor(self, organization_id: str, actor_id: str) -> list[AuditLog]:
        """Find audit logs by actor (user)"""
        return await self.find_many({
            "organization_id": organization_id,
            "actor_id": actor_id
        })

    async def find_by_resource(self, organization_id: str, resource_id: str) -> list[AuditLog]:
        """Find audit logs for resource"""
        return await self.find_many({
            "organization_id": organization_id,
            "resource_id": resource_id
        })

    async def find_by_action(self, organization_id: str, action: str) -> list[AuditLog]:
        """Find audit logs by action type"""
        return await self.find_many({
            "organization_id": organization_id,
            "action": action
        })

    async def find_failures(self, organization_id: str) -> list[AuditLog]:
        """Find failed actions"""
        return await self.find_many({
            "organization_id": organization_id,
            "success": False
        })


class NotificationRepository(BaseRepository[Notification]):
    """Repository for notifications"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.NOTIFICATIONS.value, Notification)

    async def find_by_recipient(
        self, organization_id: str, recipient_id: str, skip: int = 0, limit: int = 20
    ) -> list[Notification]:
        """Find notifications for a member"""
        return await self.find_many(
            {
                "organization_id": organization_id,
                "recipient_id": recipient_id
            },
            skip=skip,
            limit=limit
        )

    async def find_unread(self, organization_id: str, recipient_id: str) -> list[Notification]:
        """Find unread notifications"""
        return await self.find_many({
            "organization_id": organization_id,
            "recipient_id": recipient_id,
            "read": False
        })

    async def count_unread(self, organization_id: str, recipient_id: str) -> int:
        """Count unread notifications"""
        return await self.count({
            "organization_id": organization_id,
            "recipient_id": recipient_id,
            "read": False
        })

    async def find_pending(self, organization_id: str) -> list[Notification]:
        """Find notifications pending delivery"""
        return await self.find_many({
            "organization_id": organization_id,
            "status": "pending"
        })

    async def find_failed(self, organization_id: str, max_retries: int = 3) -> list[Notification]:
        """Find notifications that failed and can be retried"""
        return await self.find_many({
            "organization_id": organization_id,
            "status": "failed",
            "attempt_count": {"$lt": max_retries}
        })

    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        return await self.update(
            notification_id,
            {
                "read": True,
                "read_at": datetime.now(timezone.utc)
            }
        )

    async def mark_as_clicked(self, notification_id: str) -> bool:
        """Mark notification as clicked"""
        return await self.update(
            notification_id,
            {
                "clicked_at": datetime.now(timezone.utc)
            }
        )

    async def mark_as_sent(self, notification_id: str) -> bool:
        """Mark notification as sent"""
        return await self.update(
            notification_id,
            {
                "status": "sent",
                "sent_at": datetime.now(timezone.utc)
            }
        )

    async def mark_as_delivered(self, notification_id: str) -> bool:
        """Mark notification as delivered"""
        return await self.update(
            notification_id,
            {
                "status": "delivered",
                "delivered_at": datetime.now(timezone.utc)
            }
        )

    async def mark_as_failed(self, notification_id: str, error_message: str) -> bool:
        """Mark notification as failed"""
        return await self.update(
            notification_id,
            {
                "status": "failed",
                "last_error": error_message,
                "last_attempt_at": datetime.now(timezone.utc),
                "attempt_count": {"$inc": 1}  # Increment attempt count
            }
        )
