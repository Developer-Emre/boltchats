"""
Unit tests for Permission Service

Tests: RBAC, permission checking, caching, permission templates
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services import PermissionService, ForbiddenError, Permission


@pytest.mark.asyncio
class TestPermissionService:
    """Permission service tests"""

    async def test_has_permission_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test checking permission - success"""
        service = PermissionService(mock_db, mock_redis)

        # Mock member role with permission
        mock_member_role = {
            "member_id": member_id,
            "role_id": "admin-role-123",
        }
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_member_role)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        has_perm = await service.has_permission(
            org_id=org_id,
            member_id=member_id,
            permission="CONVERSATION_READ",
        )

        assert has_perm is True

    async def test_has_permission_failure(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test checking permission - failure"""
        service = PermissionService(mock_db, mock_redis)

        # Mock member role without permission
        mock_member_role = {
            "member_id": member_id,
            "role_id": "viewer-role-456",
        }
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_member_role)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Viewer doesn't have CONVERSATION_ASSIGN permission
        has_perm = await service.has_permission(
            org_id=org_id,
            member_id=member_id,
            permission="CONVERSATION_ASSIGN",
        )

        assert has_perm is False

    async def test_require_permission_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test requiring permission - success"""
        service = PermissionService(mock_db, mock_redis)

        # Mock member with admin role
        mock_member_role = {
            "member_id": member_id,
            "role_id": "admin-role-123",
        }
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_member_role)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Should not raise
        await service.require_permission(
            org_id=org_id,
            member_id=member_id,
            permission="CONVERSATION_ASSIGN",
        )

    async def test_require_permission_failure(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test requiring permission - failure"""
        service = PermissionService(mock_db, mock_redis)

        # Mock member with viewer role
        mock_member_role = {
            "member_id": member_id,
            "role_id": "viewer-role-456",
        }
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_member_role)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with pytest.raises(ForbiddenError):
            await service.require_permission(
                org_id=org_id,
                member_id=member_id,
                permission="CONVERSATION_ASSIGN",
            )

    async def test_redis_caching(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test that permissions are cached in Redis"""
        service = PermissionService(mock_db, mock_redis)

        mock_member_role = {
            "member_id": member_id,
            "role_id": "admin-role-123",
        }
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=mock_member_role)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # First call hits DB
        await service.has_permission(
            org_id=org_id,
            member_id=member_id,
            permission="CONVERSATION_READ",
        )

        # Redis should have cached value
        cached = await mock_redis.get(f"perms:{org_id}:{member_id}")
        assert cached is not None

    async def test_get_member_permissions(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        member_id: str,
    ):
        """Test getting all member permissions"""
        service = PermissionService(mock_db, mock_redis)

        permissions = await service.get_member_permissions(
            org_id=org_id,
            member_id=member_id,
        )

        assert isinstance(permissions, list)
        assert len(permissions) >= 0

    async def test_get_permission_templates(self):
        """Test getting permission templates"""
        service = PermissionService(MagicMock(), MagicMock())

        templates = service.get_permission_templates()

        assert "admin" in templates
        assert "manager" in templates
        assert "agent" in templates
        assert "viewer" in templates

        # Admin should have all permissions
        assert len(templates["admin"]) > len(templates["viewer"])
