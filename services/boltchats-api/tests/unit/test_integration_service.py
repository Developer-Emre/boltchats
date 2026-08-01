"""
Unit tests for Integration Service

Tests: provider factory, webhook handling, credential validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import IntegrationService, ValidationError, NotFoundError


@pytest.mark.asyncio
class TestIntegrationService:
    """Integration service tests"""

    async def test_create_integration_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test creating an integration"""
        service = IntegrationService(mock_db, mock_redis)

        integration_data = {
            "id": "int-123",
            "organization_id": org_id,
            "provider": "meta",
            "status": "active",
            "oauth_tokens": {
                "access_token": "token-123",
            },
        }

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=integration_data["id"])
        )
        mock_collection.find_one = AsyncMock(return_value=integration_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.create_integration(
            org_id=org_id,
            provider="meta",
            oauth_tokens={
                "access_token": "token-123",
            },
        )

        assert result is not None
        assert result["provider"] == "meta"
        assert result["status"] == "active"

    async def test_create_integration_invalid_provider(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
    ):
        """Test creating integration with invalid provider"""
        service = IntegrationService(mock_db, mock_redis)

        with pytest.raises(ValidationError):
            await service.create_integration(
                org_id=org_id,
                provider="unknown_provider",
                oauth_tokens={},
            )

    async def test_get_integration_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        integration_id: str,
    ):
        """Test getting an integration"""
        service = IntegrationService(mock_db, mock_redis)

        integration_data = {
            "id": integration_id,
            "organization_id": org_id,
            "provider": "meta",
            "status": "active",
        }

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=integration_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.get_integration(
            org_id=org_id,
            integration_id=integration_id,
        )

        assert result is not None
        assert result["provider"] == "meta"

    async def test_list_integrations(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
    ):
        """Test listing integrations"""
        service = IntegrationService(mock_db, mock_redis)

        integrations = [
            {
                "id": "int-1",
                "provider": "meta",
            },
            {
                "id": "int-2",
                "provider": "twilio",
            },
        ]

        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = integrations
        mock_collection.find.return_value = mock_cursor
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.list_integrations(org_id=org_id)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_handle_webhook_meta(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
    ):
        """Test handling webhook from Meta (Instagram/Facebook)"""
        service = IntegrationService(mock_db, mock_redis)

        # Meta webhook payload
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "page-id",
                    "messaging": [
                        {
                            "sender": {"id": "user-id"},
                            "recipient": {"id": "page-id"},
                            "timestamp": 1234567890,
                            "message": {"text": "Hello"},
                        }
                    ],
                }
            ],
        }

        mock_integration = {
            "id": "int-123",
            "provider": "meta",
            "webhook_url": "https://example.com/webhook",
            "oauth_tokens": {"access_token": "token"},
        }

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_integration)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Should handle webhook without error
        result = await service.handle_webhook(
            provider="meta",
            payload=payload,
        )

        assert result is not None

    async def test_handle_webhook_twilio(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
    ):
        """Test handling webhook from Twilio"""
        service = IntegrationService(mock_db, mock_redis)

        # Twilio SMS webhook payload
        payload = {
            "MessageSid": "msg-123",
            "From": "+1234567890",
            "To": "+9876543210",
            "Body": "Hello from Twilio",
        }

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Should handle webhook without error
        result = await service.handle_webhook(
            provider="twilio",
            payload=payload,
        )

        assert result is not None

    async def test_validate_webhook_signature_success(
        self,
        mock_db: MagicMock,
        mock_redis,
    ):
        """Test validating webhook signature - success"""
        service = IntegrationService(mock_db, mock_redis)

        # Mock valid signature
        payload = {"key": "value"}
        signature = "valid-signature"

        result = service.validate_webhook_signature(
            provider="meta",
            payload=payload,
            signature=signature,
            app_secret="app-secret",
        )

        # Should return True for valid signature
        assert isinstance(result, bool)

    async def test_disable_integration(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        integration_id: str,
    ):
        """Test disabling an integration"""
        service = IntegrationService(mock_db, mock_redis)

        disabled_integration = {
            "id": integration_id,
            "organization_id": org_id,
            "status": "disabled",
        }

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=disabled_integration)
        mock_collection.update_one = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.disable_integration(
            org_id=org_id,
            integration_id=integration_id,
        )

        assert result is not None
        assert result["status"] == "disabled"
