"""
Notification Service

Send and track notifications across multiple channels (email, SMS, push, in-app)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import Notification, NotificationChannel, NotificationStatus
from app.repositories import NotificationRepository

from .base import BaseService, NotFoundError


class NotificationProvider(str, Enum):
    """Notification delivery providers"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationService(BaseService):
    """Send and track notifications"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.notifications = NotificationRepository(db)

    async def send_notification(
        self,
        org_id: str,
        recipient_id: str,  # member_id or customer_id depending on context
        channel: NotificationChannel,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """
        Send notification to recipient.
        
        This is async—notification queuing, not delivery.
        Delivery happens through provider webhooks.
        
        Args:
            org_id: Organization ID
            recipient_id: Who gets the notification
            channel: Delivery channel (email, sms, push, in_app)
            title: Notification title
            message: Notification body
            data: Extra context (conversation_id, message_id, etc)
        
        Returns:
            notification_id
        """
        notification = Notification(
            organization_id=org_id,
            recipient_id=recipient_id,
            channel=channel,
            title=title,
            message=message,
            data=data or {},
            status=NotificationStatus.PENDING,
        )

        notification_id = await self.notifications.create(notification)

        await self.log_action(
            "notification_sent",
            resource_id=notification_id,
            resource_type="notification",
            details={"channel": channel, "recipient_id": recipient_id},
        )

        self.logger.info(
            "notification_queued",
            notification_id=notification_id,
            channel=channel,
            recipient_id=recipient_id,
        )

        return notification_id

    async def send_new_message_notification(
        self,
        org_id: str,
        member_id: str,
        conv_id: str,
        customer_name: str,
        message_preview: str,
        channels: list[NotificationChannel] = None,
    ) -> list[str]:
        """Send "new message" notification to team member."""
        if channels is None:
            channels = [
                NotificationChannel.IN_APP,
                NotificationChannel.EMAIL,
            ]

        notification_ids = []
        for channel in channels:
            notif_id = await self.send_notification(
                org_id=org_id,
                recipient_id=member_id,
                channel=channel,
                title=f"New message from {customer_name}",
                message=message_preview[:100],
                data={
                    "type": "new_message",
                    "conversation_id": conv_id,
                    "customer_name": customer_name,
                },
            )
            notification_ids.append(notif_id)

        return notification_ids

    async def send_assignment_notification(
        self,
        org_id: str,
        member_id: str,
        conv_id: str,
        customer_name: str,
        assigned_by: str,
    ) -> list[str]:
        """Send "conversation assigned" notification."""
        channels = [
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
        ]

        notification_ids = []
        for channel in channels:
            notif_id = await self.send_notification(
                org_id=org_id,
                recipient_id=member_id,
                channel=channel,
                title=f"Conversation assigned: {customer_name}",
                message=f"Assigned by {assigned_by}",
                data={
                    "type": "conversation_assigned",
                    "conversation_id": conv_id,
                    "assigned_by": assigned_by,
                },
            )
            notification_ids.append(notif_id)

        return notification_ids

    async def get_notifications(
        self,
        org_id: str,
        recipient_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """Get notifications for member/customer."""
        query = {
            "organization_id": org_id,
            "recipient_id": recipient_id,
        }

        if unread_only:
            query["read_at"] = None

        notifications = await self.notifications.find(query)
        return notifications[offset : offset + limit]

    async def mark_as_read(self, notification_id: str) -> Notification:
        """Mark notification as read."""
        notif = await self.notifications.read(notification_id)
        if not notif:
            raise NotFoundError("Notification", notification_id)

        await self.notifications.update(notification_id, {
            "read_at": datetime.now(timezone.utc),
        })

        return await self.notifications.read(notification_id)

    async def mark_as_clicked(self, notification_id: str) -> Notification:
        """Mark notification as clicked (user took action)."""
        notif = await self.notifications.read(notification_id)
        if not notif:
            raise NotFoundError("Notification", notification_id)

        await self.notifications.update(notification_id, {
            "clicked_at": datetime.now(timezone.utc),
        })

        return await self.notifications.read(notification_id)

    async def mark_delivery_success(
        self,
        notification_id: str,
        provider: NotificationProvider,
        external_id: Optional[str] = None,
    ) -> Notification:
        """Mark as successfully delivered by provider."""
        await self.notifications.update(notification_id, {
            "status": NotificationStatus.DELIVERED,
            "delivered_at": datetime.now(timezone.utc),
            "provider": provider,
            "provider_external_id": external_id,
        })

        return await self.notifications.read(notification_id)

    async def mark_delivery_failed(
        self,
        notification_id: str,
        error: str,
        retry_count: int = 0,
    ) -> Notification:
        """Mark as delivery failed."""
        status = NotificationStatus.FAILED
        if retry_count < 3:
            status = NotificationStatus.RETRYING

        await self.notifications.update(notification_id, {
            "status": status,
            "failed_at": datetime.now(timezone.utc),
            "error_message": error,
            "retry_count": retry_count,
        })

        return await self.notifications.read(notification_id)

    async def get_pending_notifications(
        self,
        org_id: str,
        limit: int = 100,
    ) -> list[Notification]:
        """Get notifications waiting to be sent."""
        notifications = await self.notifications.find({
            "organization_id": org_id,
            "status": NotificationStatus.PENDING,
        })
        return notifications[:limit]

    async def get_failed_notifications(
        self,
        org_id: str,
        limit: int = 100,
    ) -> list[Notification]:
        """Get failed notifications for retry."""
        notifications = await self.notifications.find({
            "organization_id": org_id,
            "status": NotificationStatus.FAILED,
        })
        return notifications[:limit]

    async def retry_failed_notification(
        self,
        notification_id: str,
    ) -> Notification:
        """Reset failed notification for retry."""
        notif = await self.notifications.read(notification_id)
        if not notif:
            raise NotFoundError("Notification", notification_id)

        retry_count = (notif.retry_count or 0) + 1
        
        if retry_count > 3:
            raise ValueError("Max retries exceeded")

        await self.notifications.update(notification_id, {
            "status": NotificationStatus.PENDING,
            "retry_count": retry_count,
        })

        return await self.notifications.read(notification_id)

    async def delete_old_notifications(
        self,
        org_id: str,
        days: int = 30,
    ) -> int:
        """Delete read notifications older than N days."""
        from datetime import timedelta
        from bson import ObjectId
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Find old read notifications
        old_notifications = await self.notifications.find({
            "organization_id": org_id,
            "read_at": {"$exists": True},
            "created_at": {"$lt": cutoff},
        })

        count = 0
        for notif in old_notifications:
            await self.notifications.delete(notif.id)
            count += 1

        self.logger.info(
            "old_notifications_deleted",
            org_id=org_id,
            count=count,
            days=days,
        )

        return count
