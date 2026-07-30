"""
Permission Service

Role-Based Access Control (RBAC)
"""

from enum import Enum
from typing import Optional

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories import MemberRoleRepository, RoleRepository
from app.services.base import BaseService, ForbiddenError, NotFoundError
from app.utils.sparkquark_constants import RedisKeys


class Permission(str, Enum):
    """All permissions in SparkQuark"""

    # Organization
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"

    # Workspace
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    WORKSPACE_DELETE = "workspace:delete"

    # Members
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"
    MEMBER_DELETE = "member:delete"

    # Teams
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    TEAM_DELETE = "team:delete"

    # Roles
    ROLE_READ = "role:read"
    ROLE_WRITE = "role:write"
    ROLE_DELETE = "role:delete"

    # Conversations
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_WRITE = "conversation:write"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_ASSIGN = "conversation:assign"
    CONVERSATION_CLOSE = "conversation:close"

    # Messages
    MESSAGE_READ = "message:read"
    MESSAGE_WRITE = "message:write"
    MESSAGE_DELETE = "message:delete"
    MESSAGE_EDIT = "message:edit"

    # Customers
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    CUSTOMER_DELETE = "customer:delete"

    # Labels
    LABEL_READ = "label:read"
    LABEL_WRITE = "label:write"
    LABEL_DELETE = "label:delete"

    # Integrations
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"
    INTEGRATION_DELETE = "integration:delete"
    INTEGRATION_CONNECT = "integration:connect"

    # Notifications
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_WRITE = "notification:write"

    # Audit & Admin
    AUDIT_READ = "audit:read"
    ADMIN_OVERRIDE = "admin:override"


class PermissionService(BaseService):
    """Check permissions and enforce access control"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
    ):
        super().__init__(db)
        self.member_roles = MemberRoleRepository(db)
        self.roles = RoleRepository(db)
        self.redis = redis_client

    async def has_permission(
        self,
        member_id: str,
        permission: Permission,
        org_id: str,
    ) -> bool:
        """
        Check if member has permission.
        
        Checks:
        1. Redis cache (performance)
        2. Database (roles → permissions)
        
        Args:
            member_id: Member ID
            permission: Permission code
            org_id: Organization ID (for audit)
            
        Returns:
            True if has permission, False otherwise
        """
        # Check cache first (Redis)
        cache_key = f"{RedisKeys.PERMISSIONS}:{member_id}"
        cached_perms = await self.redis.get(cache_key)

        if cached_perms:
            # Parse cached permissions
            perms_set = set(cached_perms.decode().split(","))
            return permission in perms_set

        # Fetch from database
        member_perms = await self._get_member_permissions(member_id)

        # Cache for 1 hour
        await self.redis.setex(
            cache_key,
            3600,
            ",".join(member_perms),
        )

        return permission in member_perms

    async def require_permission(
        self,
        member_id: str,
        permission: Permission,
        org_id: str,
    ) -> None:
        """
        Assert member has permission.
        
        Raises ForbiddenError if not.
        
        Args:
            member_id: Member ID
            permission: Permission code
            org_id: Organization ID
            
        Raises:
            ForbiddenError: No permission
        """
        has_perm = await self.has_permission(member_id, permission, org_id)

        if not has_perm:
            self.logger.warning(
                "permission_denied",
                member_id=member_id,
                permission=permission,
                org_id=org_id,
            )
            raise ForbiddenError(f"No permission: {permission}")

    async def require_any_permission(
        self,
        member_id: str,
        permissions: list[Permission],
        org_id: str,
    ) -> None:
        """
        Assert member has ANY of the permissions.
        
        Args:
            member_id: Member ID
            permissions: List of permission codes
            org_id: Organization ID
            
        Raises:
            ForbiddenError: No matching permission
        """
        member_perms = await self._get_member_permissions(member_id)

        for perm in permissions:
            if perm in member_perms:
                return  # Has at least one

        raise ForbiddenError(
            f"No permission. Required one of: {[p for p in permissions]}"
        )

    async def require_all_permissions(
        self,
        member_id: str,
        permissions: list[Permission],
        org_id: str,
    ) -> None:
        """
        Assert member has ALL of the permissions.
        
        Args:
            member_id: Member ID
            permissions: List of permission codes
            org_id: Organization ID
            
        Raises:
            ForbiddenError: Missing any permission
        """
        member_perms = await self._get_member_permissions(member_id)

        for perm in permissions:
            if perm not in member_perms:
                raise ForbiddenError(f"No permission: {perm}")

    async def get_member_permissions(
        self,
        member_id: str,
    ) -> set[Permission]:
        """
        Get all permissions for member.
        
        Args:
            member_id: Member ID
            
        Returns:
            Set of Permission codes
        """
        perms = await self._get_member_permissions(member_id)
        return set(perms)

    async def _get_member_permissions(self, member_id: str) -> list[str]:
        """
        Get member's permissions from database.
        
        Loads all roles and their permissions.
        """
        # Get member's roles
        member_roles = await self.member_roles.find({
            "member_id": member_id,
        })

        if not member_roles:
            return []

        # Get all permissions from all roles
        all_permissions = set()

        for member_role in member_roles:
            # Skip expired roles
            if member_role.expires_at:
                from datetime import datetime, timezone
                if member_role.expires_at < datetime.now(timezone.utc):
                    continue

            # Get role
            role = await self.roles.read(member_role.role_id)
            if role and role.permissions:
                all_permissions.update(role.permissions)

        return list(all_permissions)

    async def invalidate_member_permissions(self, member_id: str) -> None:
        """
        Invalidate permission cache for member.
        
        Call after role changes.
        
        Args:
            member_id: Member ID
        """
        cache_key = f"{RedisKeys.PERMISSIONS}:{member_id}"
        await self.redis.delete(cache_key)

        self.logger.info(
            "permissions_invalidated",
            member_id=member_id,
        )

    async def invalidate_org_permissions(self, org_id: str) -> None:
        """
        Invalidate permission cache for entire organization.
        
        Call after role changes affecting multiple members.
        
        Args:
            org_id: Organization ID
        """
        # This is a wildcard operation
        # In production, might need to track member IDs per org
        # For now, just log
        self.logger.info(
            "org_permissions_invalidated",
            org_id=org_id,
        )

    # ─── PERMISSION TEMPLATES ──────────────────────────────────────────

    @staticmethod
    def get_default_permissions(role_name: str) -> list[Permission]:
        """
        Get default permissions for a role.
        
        Args:
            role_name: Role name (admin, manager, agent, viewer)
            
        Returns:
            List of default permissions
        """
        templates = {
            "admin": [
                # All permissions
                Permission.ORG_READ,
                Permission.ORG_WRITE,
                Permission.ORG_DELETE,
                Permission.WORKSPACE_READ,
                Permission.WORKSPACE_WRITE,
                Permission.WORKSPACE_DELETE,
                Permission.MEMBER_READ,
                Permission.MEMBER_WRITE,
                Permission.MEMBER_DELETE,
                Permission.TEAM_READ,
                Permission.TEAM_WRITE,
                Permission.TEAM_DELETE,
                Permission.ROLE_READ,
                Permission.ROLE_WRITE,
                Permission.ROLE_DELETE,
                Permission.CONVERSATION_READ,
                Permission.CONVERSATION_WRITE,
                Permission.CONVERSATION_DELETE,
                Permission.CONVERSATION_ASSIGN,
                Permission.CONVERSATION_CLOSE,
                Permission.MESSAGE_READ,
                Permission.MESSAGE_WRITE,
                Permission.MESSAGE_DELETE,
                Permission.MESSAGE_EDIT,
                Permission.CUSTOMER_READ,
                Permission.CUSTOMER_WRITE,
                Permission.CUSTOMER_DELETE,
                Permission.LABEL_READ,
                Permission.LABEL_WRITE,
                Permission.LABEL_DELETE,
                Permission.INTEGRATION_READ,
                Permission.INTEGRATION_WRITE,
                Permission.INTEGRATION_DELETE,
                Permission.INTEGRATION_CONNECT,
                Permission.NOTIFICATION_READ,
                Permission.NOTIFICATION_WRITE,
                Permission.AUDIT_READ,
                Permission.ADMIN_OVERRIDE,
            ],
            "manager": [
                # Team & customer management
                Permission.ORG_READ,
                Permission.WORKSPACE_READ,
                Permission.WORKSPACE_WRITE,
                Permission.MEMBER_READ,
                Permission.MEMBER_WRITE,
                Permission.TEAM_READ,
                Permission.TEAM_WRITE,
                Permission.CONVERSATION_READ,
                Permission.CONVERSATION_WRITE,
                Permission.CONVERSATION_ASSIGN,
                Permission.CONVERSATION_CLOSE,
                Permission.MESSAGE_READ,
                Permission.MESSAGE_WRITE,
                Permission.CUSTOMER_READ,
                Permission.CUSTOMER_WRITE,
                Permission.LABEL_READ,
                Permission.LABEL_WRITE,
                Permission.NOTIFICATION_READ,
                Permission.AUDIT_READ,
            ],
            "agent": [
                # Handle conversations & messages only
                Permission.CONVERSATION_READ,
                Permission.CONVERSATION_WRITE,
                Permission.MESSAGE_READ,
                Permission.MESSAGE_WRITE,
                Permission.MESSAGE_EDIT,
                Permission.CUSTOMER_READ,
                Permission.LABEL_READ,
                Permission.NOTIFICATION_READ,
            ],
            "viewer": [
                # Read-only access
                Permission.CONVERSATION_READ,
                Permission.MESSAGE_READ,
                Permission.CUSTOMER_READ,
                Permission.LABEL_READ,
                Permission.AUDIT_READ,
            ],
        }

        return templates.get(role_name, [])
