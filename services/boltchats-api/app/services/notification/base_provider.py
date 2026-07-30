"""
Base Notification Provider

Abstract base class for notification providers
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseNotificationProvider(ABC):
    """Abstract base for notification providers"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def validate_credentials(self, credentials: dict) -> bool:
        """Validate provider credentials."""
        pass

    @abstractmethod
    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """
        Send notification.
        
        Args:
            recipient_id: Recipient identifier (email, user ID, etc)
            title: Notification title
            message: Notification message
            data: Extra data
            
        Returns:
            Provider message ID
        """
        pass

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> dict:
        """Handle webhook from provider (delivery status, etc)."""
        pass

    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> Optional[dict]:
        """Get delivery status of notification."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if provider connection is valid."""
        pass
