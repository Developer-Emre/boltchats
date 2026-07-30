"""
Notification Provider Factory

Factory for creating notification provider instances
"""

import redis.asyncio as redis

from app.services.base import ValidationError

from .base_provider import BaseNotificationProvider
from .email_provider import EmailNotificationProvider
from .push_provider import PushNotificationProvider
from .websocket_provider import WebSocketNotificationProvider


class NotificationProviderFactory:
    """Factory for creating notification providers"""

    @staticmethod
    def create_provider(
        provider_name: str,
        credentials: dict,
        redis_client: redis.Redis | None = None,
    ) -> BaseNotificationProvider:
        """
        Create notification provider instance.
        
        Args:
            provider_name: Provider name (email, push, websocket)
            credentials: Provider-specific credentials
            redis_client: Redis client (required for websocket)
            
        Returns:
            NotificationProvider instance
            
        Raises:
            ValidationError: Unknown provider or missing credentials
        """
        provider_name = provider_name.lower()

        if provider_name == "email":
            api_key = credentials.get("api_key")
            from_email = credentials.get("from_email")
            provider = credentials.get("provider", "sendgrid")

            if not api_key or not from_email:
                raise ValidationError("Email requires: api_key, from_email")

            return EmailNotificationProvider(api_key, from_email, provider)

        elif provider_name == "push":
            api_key = credentials.get("api_key")
            provider = credentials.get("provider", "fcm")

            if not api_key:
                raise ValidationError("Push requires: api_key")

            return PushNotificationProvider(api_key, provider)

        elif provider_name == "websocket":
            if not redis_client:
                raise ValidationError("WebSocket requires Redis client")

            return WebSocketNotificationProvider(redis_client)

        else:
            raise ValidationError(f"Unknown notification provider: {provider_name}")

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported notification providers."""
        return ["email", "push", "websocket"]

    @staticmethod
    def get_required_credentials(provider_name: str) -> dict:
        """
        Get required credentials for provider.
        
        Returns:
            {field: description}
        """
        specs = {
            "email": {
                "api_key": "SendGrid/Mailgun API key",
                "from_email": "From email address",
                "provider": "Provider type (sendgrid, mailgun, smtp)",
            },
            "push": {
                "api_key": "Firebase or OneSignal API key",
                "provider": "Provider type (fcm, onesignal)",
            },
            "websocket": {
                "redis": "Redis client (automatic)",
            },
        }

        return specs.get(provider_name.lower(), {})
