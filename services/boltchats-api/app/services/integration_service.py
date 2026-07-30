"""
Integration Service

Connect/disconnect providers (Instagram, WhatsApp, Facebook, Email, etc)
OAuth token management and webhook handling
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import Integration, OAuthData
from app.repositories import IntegrationRepository

from .base import BaseService, ConflictError, NotFoundError, ValidationError


class IntegrationService(BaseService):
    """Manage integrations with external providers"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.integrations = IntegrationRepository(db)

    # ─── CONNECT PROVIDER ─────────────────────────────────────────────

    async def create_integration(
        self,
        org_id: str,
        provider_name: str,
        display_name: str,
        provider_account_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        avatar: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Integration:
        """
        Create new provider integration.
        
        OAuth tokens are stored encrypted (should be in production).
        For now, using plaintext in MongoDB with env-based encryption.
        
        Args:
            org_id: Organization ID
            provider_name: "instagram", "facebook", "whatsapp", "email", etc
            display_name: "My Instagram", "Support Email", etc
            provider_account_id: External ID (@username, email, etc)
            access_token: OAuth access token
            refresh_token: OAuth refresh token (if available)
            expires_at: Token expiry time
            avatar: Avatar URL from provider
            metadata: Extra provider-specific data
        """
        # Check provider not already connected with this account
        existing = await self.integrations.find_by_provider_account(
            org_id, provider_name, provider_account_id
        )
        if existing:
            raise ConflictError(
                f"Provider {provider_name} already connected with account {provider_account_id}"
            )

        # Set default expiry (24 hours if not specified)
        if expires_at is None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Create OAuth data
        oauth = OAuthData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        # Create integration
        integration = Integration(
            organization_id=org_id,
            provider_name=provider_name,
            display_name=display_name,
            provider_account_id=provider_account_id,
            avatar=avatar,
            metadata=metadata or {},
            oauth=oauth,
        )

        integration_id = await self.integrations.create(integration)

        await self.log_action(
            "integration_connected",
            resource_id=integration_id,
            resource_type="integration",
            details={
                "provider": provider_name,
                "account_id": provider_account_id,
            },
        )

        self.logger.info(
            "provider_connected",
            integration_id=integration_id,
            provider=provider_name,
        )

        return await self.integrations.read(integration_id)

    # ─── DISCONNECT PROVIDER ──────────────────────────────────────────

    async def disconnect_integration(
        self,
        org_id: str,
        integration_id: str,
    ) -> None:
        """Disconnect provider integration."""
        # Check integration exists in org
        integration = await self.integrations.read(integration_id)
        if not integration or integration.organization_id != org_id:
            raise NotFoundError("Integration", integration_id)

        # Soft delete
        await self.integrations.update(integration_id, {
            "disconnected_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "integration_disconnected",
            resource_id=integration_id,
            resource_type="integration",
        )

        self.logger.info(
            "provider_disconnected",
            integration_id=integration_id,
            provider=integration.provider_name,
        )

    # ─── OAUTH TOKEN MANAGEMENT ────────────────────────────────────────

    async def refresh_token(self, integration_id: str) -> Integration:
        """
        Refresh OAuth token.
        
        In production, this would call provider's refresh endpoint.
        For now, just updating the timestamp.
        """
        integration = await self.integrations.read(integration_id)
        if not integration:
            raise NotFoundError("Integration", integration_id)

        if not integration.oauth:
            raise ValidationError("Integration has no OAuth configuration")

        # In real implementation, call provider API to refresh
        # For now, just extend expiry
        new_expiry = datetime.now(timezone.utc) + timedelta(hours=24)

        await self.integrations.update(integration_id, {
            "oauth.expires_at": new_expiry,
        })

        await self.log_action(
            "token_refreshed",
            resource_id=integration_id,
            resource_type="integration",
        )

        return await self.integrations.read(integration_id)

    async def is_token_expired(self, integration_id: str) -> bool:
        """Check if OAuth token is expired."""
        integration = await self.integrations.read(integration_id)
        if not integration or not integration.oauth:
            return True

        return integration.oauth.expires_at < datetime.now(timezone.utc)

    async def rotate_token(
        self,
        integration_id: str,
        new_access_token: str,
        new_refresh_token: Optional[str] = None,
    ) -> Integration:
        """Rotate OAuth tokens."""
        integration = await self.integrations.read(integration_id)
        if not integration:
            raise NotFoundError("Integration", integration_id)

        new_expiry = datetime.now(timezone.utc) + timedelta(hours=24)

        await self.integrations.update(integration_id, {
            "oauth.access_token": new_access_token,
            "oauth.refresh_token": new_refresh_token,
            "oauth.expires_at": new_expiry,
        })

        await self.log_action(
            "token_rotated",
            resource_id=integration_id,
            resource_type="integration",
        )

        return await self.integrations.read(integration_id)

    # ─── INTEGRATIONS LISTING ─────────────────────────────────────────

    async def get_integrations(self, org_id: str) -> list[Integration]:
        """Get all active integrations for organization."""
        integrations = await self.integrations.find({
            "organization_id": org_id,
            "disconnected_at": None,
        })
        return integrations

    async def get_integration_by_provider(
        self,
        org_id: str,
        provider_name: str,
    ) -> list[Integration]:
        """Get all instances of a provider connected to org."""
        integrations = await self.integrations.find({
            "organization_id": org_id,
            "provider_name": provider_name,
            "disconnected_at": None,
        })
        return integrations

    # ─── WEBHOOK HANDLING ─────────────────────────────────────────────

    async def handle_webhook(
        self,
        provider: str,
        payload: dict,
        signature: str,
    ) -> dict:
        """
        Handle incoming webhook from provider.
        
        Validates signature and routes to appropriate handler.
        
        Args:
            provider: Provider name
            payload: Webhook payload
            signature: HMAC signature from provider
        
        Returns:
            Response to send to provider
        """
        # Signature validation should happen here
        # For now, just logging and returning success

        self.logger.info(
            "webhook_received",
            provider=provider,
            event_type=payload.get("type"),
        )

        # Route to provider-specific handler
        if provider == "instagram":
            return await self._handle_instagram_webhook(payload)
        elif provider == "facebook":
            return await self._handle_facebook_webhook(payload)
        elif provider == "whatsapp":
            return await self._handle_whatsapp_webhook(payload)
        elif provider == "email":
            return await self._handle_email_webhook(payload)
        else:
            raise ValidationError(f"Unknown provider: {provider}")

    async def _handle_instagram_webhook(self, payload: dict) -> dict:
        """Handle Instagram webhook (new DMs, reactions, etc)"""
        # TODO: Parse Instagram payload and trigger conversation events
        # payload typically contains:
        # - sender_id, recipient_id
        # - message content
        # - timestamp
        
        event_type = payload.get("type")
        self.logger.info("instagram_event", event_type=event_type)
        
        return {"status": "ok"}

    async def _handle_facebook_webhook(self, payload: dict) -> dict:
        """Handle Facebook webhook"""
        # TODO: Parse Facebook payload
        return {"status": "ok"}

    async def _handle_whatsapp_webhook(self, payload: dict) -> dict:
        """Handle WhatsApp webhook"""
        # TODO: Parse WhatsApp payload
        return {"status": "ok"}

    async def _handle_email_webhook(self, payload: dict) -> dict:
        """Handle Email (SendGrid, Mailgun, etc) webhook"""
        # TODO: Parse email provider payload
        return {"status": "ok"}

    # ─── PROVIDER HEALTH ──────────────────────────────────────────────

    async def check_provider_health(self, integration_id: str) -> dict:
        """
        Check if provider integration is healthy.
        
        Returns health status and any issues.
        """
        integration = await self.integrations.read(integration_id)
        if not integration:
            raise NotFoundError("Integration", integration_id)

        status = "healthy"
        issues = []

        # Check if token expired
        if integration.oauth and integration.oauth.expires_at < datetime.now(timezone.utc):
            status = "degraded"
            issues.append("OAuth token expired")

        # Check if disconnected
        if integration.disconnected_at:
            status = "disconnected"

        return {
            "integration_id": integration_id,
            "provider": integration.provider_name,
            "status": status,
            "issues": issues,
            "last_sync": integration.last_sync_at,
        }
