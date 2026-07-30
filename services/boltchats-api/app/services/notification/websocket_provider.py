"""
WebSocket Notification Provider

In-app notifications via WebSocket
"""

from typing import Optional

import redis.asyncio as redis

from .base_provider import BaseNotificationProvider


class WebSocketNotificationProvider(BaseNotificationProvider):
    """
    In-app notification provider via WebSocket.
    
    Uses Redis Pub/Sub to broadcast notifications to connected clients.
    """

    def __init__(self, redis_client: redis.Redis):
        super().__init__("websocket")
        self.redis = redis_client

    async def validate_credentials(self, credentials: dict) -> bool:
        """WebSocket doesn't need credentials."""
        return True

    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """
        Send in-app notification via WebSocket.
        
        Args:
            recipient_id: Member ID or user ID
            title: Notification title
            message: Notification message
            data: Extra data
            
        Returns:
            Notification ID
        """
        import json
        from datetime import datetime, timezone

        notification_id = f"websocket_{recipient_id}_{int(1000000000)}"

        # Publish to Redis channel for member
        channel = f"notifications:member:{recipient_id}"
        payload = {
            "id": notification_id,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self.redis.publish(channel, json.dumps(payload))

        return notification_id

    async def handle_webhook(self, payload: dict) -> dict:
        """WebSocket doesn't receive webhooks."""
        return {"status": "ok"}

    async def get_delivery_status(self, message_id: str) -> Optional[dict]:
        """
        WebSocket messages are ephemeral.
        If no one is connected, message is lost (design choice).
        """
        return {
            "status": "unknown",
            "provider": "websocket",
            "message": "WebSocket notifications are ephemeral (not persisted)",
        }

    async def is_connected(self) -> bool:
        """WebSocket is always 'connected' (Redis is backing)."""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
