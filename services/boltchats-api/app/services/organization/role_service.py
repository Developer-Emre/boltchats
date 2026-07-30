"""
Role Service

Role and permission management
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import RoleDocument
from app.repositories import RoleRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class RoleService(BaseService):
    """Manage roles in organization"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.roles = RoleRepository(db)

    async def create_role(
        self,
        org_id: str,
        name: str,
        permissions: list[str],
        description: str = "",
    ) -> RoleDocument:
        """
        Create role in organization.
        
        Args:
            org_id: Organization ID
            name: Role name (Admin, Agent, Manager, etc)
            permissions: List of permission codes
            description: Role description
            
        Returns:
            RoleDocument
        """
        # Check name unique in org
        existing = await self.roles.find({
            "organization_id": org_id,
            "name": name,
        })
        if existing:
            raise ConflictError(f"Role '{name}' already exists")

        role = RoleDocument(
            organization_id=org_id,
            name=name,
            permissions=permissions,
            description=description,
        )
        role_id = await self.roles.create(role)

        await self.log_action(
            "role_created",
            resource_id=role_id,
            resource_type="role",
            details={"name": name},
        )

        return await self.roles.read(role_id)

    async def get_role(self, org_id: str, role_id: str) -> RoleDocument:
        """Get role."""
        role = await self.roles.read(role_id)
        if not role or role.organization_id != org_id:
            raise NotFoundError("Role", role_id)
        return role

    async def get_roles(self, org_id: str) -> list[RoleDocument]:
        """Get all roles in organization."""
        return await self.roles.find({
            "organization_id": org_id,
        })

    async def update_role(
        self,
        org_id: str,
        role_id: str,
        permissions: list[str] | None = None,
        description: str | None = None,
    ) -> RoleDocument:
        """Update role."""
        role = await self.get_role(org_id, role_id)

        update_data = {}
        if permissions is not None:
            update_data["permissions"] = permissions
        if description is not None:
            update_data["description"] = description

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.roles.update(role_id, update_data)
        return await self.roles.read(role_id)

    async def delete_role(self, org_id: str, role_id: str) -> None:
        """Delete role (soft delete)."""
        role = await self.get_role(org_id, role_id)

        await self.roles.update(role_id, {
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "role_deleted",
            resource_id=role_id,
            resource_type="role",
        )
