"""
Integration Service

Provider connection management
"""

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import Integration
from app.repositories import IntegrationRepository
from app.services.base import BaseService, ConflictError, NotFoundError

from .provider_factory import ProviderFactory


class IntegrationService(BaseService):
    """Manage provider integrations (delegates to provider adapters)"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.integrations = IntegrationRepository(db)

    async def connect_provider(
        self,
        org_id: str,
        provider_name: str,
        credentials: dict,
        display_name: Optional[str] = None,
    ) -> Integration:
        """
        Connect provider.
        
        Args:
            org_id: Organization ID
            provider_name: Provider name (instagram, facebook, whatsapp, email)
            credentials: Provider-specific credentials
            display_name: Display name for this integration
            
        Returns:
            Integration
        """
        # Validate provider exists and credentials are correct
        provider = ProviderFactory.create_provider(provider_name, credentials)

        # Validate credentials
        valid = await provider.validate_credentials(credentials)
        if not valid:
            raise ValueError(f"Invalid credentials for {provider_name}")

        # Extract provider account ID from credentials
        provider_account_id = credentials.get("provider_account_id") or credentials.get(
            "business_account_id"
        ) or credentials.get("page_id") or credentials.get("phone_number_id") or credentials.get("email")

        # Check not already connected with this account
        existing = await self.integrations.find({
            "organization_id": org_id,
            "provider_name": provider_name,
            "provider_account_id": provider_account_id,
        })
        if existing:
            raise ConflictError(
                f"{provider_name} account already connected"
            )

        # Create integration (credentials stored encrypted in production)
        integration = Integration(
            organization_id=org_id,
            provider_name=provider_name,
            display_name=display_name or f"{provider_name} - {provider_account_id}",
            provider_account_id=provider_account_id,
            metadata=credentials,
        )
        integration_id = await self.integrations.create(integration)

        await self.log_action(
            "provider_connected",
            resource_id=integration_id,
            resource_type="integration",
            details={"provider": provider_name},
        )

        return await self.integrations.read(integration_id)

    async def disconnect_provider(
        self,
        org_id: str,
        integration_id: str,
    ) -> None:
        """
        Disconnect provider.
        
        Args:
            org_id: Organization ID
            integration_id: Integration ID
        """
        integration = await self.integrations.read(integration_id)
        if not integration or integration.organization_id != org_id:
            raise NotFoundError("Integration", integration_id)

        # Get provider and disconnect
        provider = ProviderFactory.create_provider(
            integration.provider_name,
            integration.metadata,
        )
        await provider.disconnect()

        # Mark as disconnected
        await self.integrations.update(integration_id, {
            "disconnected_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "provider_disconnected",
            resource_id=integration_id,
            resource_type="integration",
        )

    async def get_provider_adapter(
        self,
        org_id: str,
        integration_id: str,
    ):
        """
        Get provider adapter for integration.
        
        Used by webhook handlers and message senders.
        """
        integration = await self.integrations.read(integration_id)
        if not integration or integration.organization_id != org_id:
            raise NotFoundError("Integration", integration_id)

        if integration.disconnected_at:
            raise ValueError("Integration is disconnected")

        return ProviderFactory.create_provider(
            integration.provider_name,
            integration.metadata,
        )

    async def handle_webhook(
        self,
        provider_name: str,
        payload: dict,
    ) -> dict:
        """
        Handle webhook from provider.
        
        Args:
            provider_name: Provider name
            payload: Webhook payload
            
        Returns:
            Response for provider
        """
        provider = ProviderFactory.create_provider(provider_name, {})
        return await provider.handle_webhook(payload)

    async def get_integrations(self, org_id: str) -> list[Integration]:
        """Get all integrations for organization."""
        return await self.integrations.find({
            "organization_id": org_id,
            "disconnected_at": None,
        })

    async def get_integration_by_provider(
        self,
        org_id: str,
        provider_name: str,
    ) -> list[Integration]:
        """Get all instances of a provider."""
        return await self.integrations.find({
            "organization_id": org_id,
            "provider_name": provider_name,
            "disconnected_at": None,
        })

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get supported provider names."""
        return ProviderFactory.get_supported_providers()

    @staticmethod
    def get_provider_requirements(provider_name: str) -> dict:
        """Get required credentials for provider."""
        return ProviderFactory.get_required_credentials(provider_name)
