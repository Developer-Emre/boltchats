"""
Notification Service

Multi-channel notification management
"""

from typing import Optional

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import Notification, NotificationChannel, NotificationStatus
from app.repositories import NotificationRepository
from app.services.base import BaseService, NotFoundError

from .provider_factory import NotificationProviderFactory


class NotificationService(BaseService):
    """Send and track notifications across channels"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
    ):
        super().__init__(db)
        self.notifications = NotificationRepository(db)
        self.redis = redis_client

    async def send_notification(
        self,
        org_id: str,
        recipient_id: str,
        channel: NotificationChannel,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """
        Send notification via channel.
        
        Args:
            org_id: Organization ID
            recipient_id: Member/user/email recipient
            channel: Channel (email, push, websocket, in_app)
            title: Notification title
            message: Notification message
            data: Extra data (conversation_id, etc)
            
        Returns:
            Notification ID
        """
        # Create notification record
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

        # Get provider for channel
        provider_name = self._channel_to_provider(channel)
        
        try:
            # Get provider configuration (from org settings or defaults)
            credentials = await self._get_provider_credentials(org_id, provider_name)
            
            # Create provider
            provider = NotificationProviderFactory.create_provider(
                provider_name,
                credentials,
                self.redis if provider_name == "websocket" else None,
            )

            # Send via provider
            provider_message_id = await provider.send_notification(
                recipient_id, title, message, data
            )

            # Update notification
            await self.notifications.update(notification_id, {
                "status": NotificationStatus.DELIVERED,
                "provider_message_id": provider_message_id,
            })

        except Exception as e:
            # Mark as failed
            await self.notifications.update(notification_id, {
                "status": NotificationStatus.FAILED,
                "error_message": str(e),
            })

        await self.log_action(
            "notification_sent",
            resource_id=notification_id,
            resource_type="notification",
            details={"channel": channel},
        )

        return notification_id

    async def get_notifications(
        self,
        org_id: str,
        recipient_id: str,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for recipient."""
        return await self.notifications.find({
            "organization_id": org_id,
            "recipient_id": recipient_id,
        })[:limit]

    async def mark_as_read(self, notification_id: str) -> Notification:
        """Mark notification as read."""
        notif = await self.notifications.read(notification_id)
        if not notif:
            raise NotFoundError("Notification", notification_id)

        from datetime import datetime, timezone
        await self.notifications.update(notification_id, {
            "read_at": datetime.now(timezone.utc),
        })

        return await self.notifications.read(notification_id)

    async def mark_as_clicked(self, notification_id: str) -> Notification:
        """Mark notification as clicked (action taken)."""
        notif = await self.notifications.read(notification_id)
        if not notif:
            raise NotFoundError("Notification", notification_id)

        from datetime import datetime, timezone
        await self.notifications.update(notification_id, {
            "clicked_at": datetime.now(timezone.utc),
        })

        return await self.notifications.read(notification_id)

    async def handle_provider_webhook(
        self,
        provider_name: str,
        payload: dict,
    ) -> dict:
        """Handle webhook from notification provider."""
        try:
            provider = NotificationProviderFactory.create_provider(
                provider_name, {}
            )
            return await provider.handle_webhook(payload)
        except Exception as e:
            self.logger.error(
                "notification_webhook_error",
                provider=provider_name,
                error=str(e),
            )
            return {"status": "error", "message": str(e)}

    def _channel_to_provider(self, channel: NotificationChannel) -> str:
        """Map notification channel to provider name."""
        mapping = {
            NotificationChannel.EMAIL: "email",
            NotificationChannel.PUSH: "push",
            NotificationChannel.IN_APP: "websocket",
        }
        return mapping.get(channel, "websocket")

    async def _get_provider_credentials(
        self,
        org_id: str,
        provider_name: str,
    ) -> dict:
        """
        Get provider credentials for organization.
        
        In production: fetch from org settings encrypted storage.
        For now: return empty dict (mock).
        """
        # TODO: Implement credential storage and retrieval
        return {}

    @staticmethod
    def get_supported_channels() -> list[str]:
        """Get supported notification channels."""
        return ["email", "push", "websocket"]
