"""
Organization Service

Organization CRUD and settings
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Organization
from app.repositories import OrganizationRepository
from app.services.base import BaseService, NotFoundError


class OrganizationService(BaseService):
    """Manage organizations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.organizations = OrganizationRepository(db)

    async def create_organization(
        self,
        name: str,
        settings: dict | None = None,
    ) -> Organization:
        """
        Create new organization.
        
        Args:
            name: Organization name
            settings: Organization settings
            
        Returns:
            Organization
        """
        org = Organization(
            name=name,
            settings=settings or {},
        )
        org_id = await self.organizations.create(org)

        await self.log_action(
            "organization_created",
            resource_id=org_id,
            resource_type="organization",
            details={"name": name},
        )

        return await self.organizations.read(org_id)

    async def get_organization(self, org_id: str) -> Organization:
        """Get organization."""
        org = await self.organizations.get_active(org_id)
        if not org:
            raise NotFoundError("Organization", org_id)
        return org

    async def update_organization(
        self,
        org_id: str,
        name: str | None = None,
        settings: dict | None = None,
    ) -> Organization:
        """Update organization settings."""
        update_data = {}
        if name:
            update_data["name"] = name
        if settings:
            update_data["settings"] = settings

        update_data["updated_at"] = datetime.now(timezone.utc)

        success = await self.organizations.update(org_id, update_data)
        if not success:
            raise NotFoundError("Organization", org_id)

        return await self.organizations.read(org_id)

    async def delete_organization(self, org_id: str) -> None:
        """Soft delete organization."""
        await self.organizations.update(org_id, {
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "organization_deleted",
            resource_id=org_id,
            resource_type="organization",
        )
