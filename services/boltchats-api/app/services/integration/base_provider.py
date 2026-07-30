"""
Base Provider

Abstract base class for all provider adapters
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseProvider(ABC):
    """Abstract base for all provider adapters"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def validate_credentials(self, credentials: dict) -> bool:
        """
        Validate provider credentials.
        
        Args:
            credentials: Provider-specific credentials
            
        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> dict:
        """
        Handle incoming webhook from provider.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Response to send to provider
        """
        pass

    @abstractmethod
    async def send_message(
        self,
        recipient_id: str,
        content: str,
        attachments: Optional[list] = None,
    ) -> str:
        """
        Send message through provider.
        
        Args:
            recipient_id: Recipient identifier
            content: Message content
            attachments: Optional attachments
            
        Returns:
            Provider message ID
        """
        pass

    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[dict]:
        """Get message details from provider."""
        pass

    @abstractmethod
    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile from provider."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from provider (cleanup)."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if provider is still connected."""
        pass

    @abstractmethod
    async def refresh_credentials(self) -> dict:
        """
        Refresh provider credentials (if supported).
        
        Returns:
            Updated credentials
        """
        pass
