"""
Workspace Service

Workspaces (Support, Sales, Marketing, etc) within organization
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Workspace
from app.repositories import OrganizationRepository, WorkspaceRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class WorkspaceService(BaseService):
    """Manage workspaces within organization"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.workspaces = WorkspaceRepository(db)
        self.organizations = OrganizationRepository(db)

    async def create_workspace(
        self,
        org_id: str,
        name: str,
        description: str = "",
    ) -> Workspace:
        """
        Create workspace in organization.
        
        Args:
            org_id: Organization ID
            name: Workspace name
            description: Workspace description
            
        Returns:
            Workspace
        """
        # Check org exists
        org = await self.organizations.get_active(org_id)
        if not org:
            raise NotFoundError("Organization", org_id)

        # Check name unique in org
        existing = await self.workspaces.find_by_name(org_id, name)
        if existing:
            raise ConflictError(f"Workspace '{name}' already exists")

        workspace = Workspace(
            organization_id=org_id,
            name=name,
            description=description,
        )
        workspace_id = await self.workspaces.create(workspace)

        await self.log_action(
            "workspace_created",
            resource_id=workspace_id,
            resource_type="workspace",
            details={"org_id": org_id, "name": name},
        )

        return await self.workspaces.read(workspace_id)

    async def get_workspace(self, org_id: str, workspace_id: str) -> Workspace:
        """Get workspace."""
        workspace = await self.workspaces.read(workspace_id)
        if not workspace or workspace.organization_id != org_id:
            raise NotFoundError("Workspace", workspace_id)
        return workspace

    async def get_workspaces(self, org_id: str) -> list[Workspace]:
        """Get all workspaces in organization."""
        return await self.workspaces.find_by_org(org_id)

    async def update_workspace(
        self,
        org_id: str,
        workspace_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Workspace:
        """Update workspace."""
        workspace = await self.get_workspace(org_id, workspace_id)

        update_data = {}
        if name:
            # Check new name unique
            existing = await self.workspaces.find_by_name(org_id, name)
            if existing and existing.id != workspace_id:
                raise ConflictError(f"Workspace '{name}' already exists")
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.workspaces.update(workspace_id, update_data)
        return await self.workspaces.read(workspace_id)

    async def delete_workspace(self, org_id: str, workspace_id: str) -> None:
        """Soft delete workspace."""
        workspace = await self.get_workspace(org_id, workspace_id)

        await self.workspaces.update(workspace_id, {
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "workspace_deleted",
            resource_id=workspace_id,
            resource_type="workspace",
        )
