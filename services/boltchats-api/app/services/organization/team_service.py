"""
Team Service

Team management within organization
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Team
from app.repositories import OrganizationRepository, TeamRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class TeamService(BaseService):
    """Manage teams in organization"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.teams = TeamRepository(db)
        self.organizations = OrganizationRepository(db)

    async def create_team(
        self,
        org_id: str,
        name: str,
        description: str = "",
    ) -> Team:
        """
        Create team in organization.
        
        Args:
            org_id: Organization ID
            name: Team name
            description: Team description
            
        Returns:
            Team
        """
        # Check org exists
        org = await self.organizations.get_active(org_id)
        if not org:
            raise NotFoundError("Organization", org_id)

        # Check name unique in org
        existing = await self.teams.find_by_name(org_id, name)
        if existing:
            raise ConflictError(f"Team '{name}' already exists")

        team = Team(
            organization_id=org_id,
            name=name,
            description=description,
        )
        team_id = await self.teams.create(team)

        await self.log_action(
            "team_created",
            resource_id=team_id,
            resource_type="team",
            details={"name": name},
        )

        return await self.teams.read(team_id)

    async def get_team(self, org_id: str, team_id: str) -> Team:
        """Get team."""
        team = await self.teams.read(team_id)
        if not team or team.organization_id != org_id:
            raise NotFoundError("Team", team_id)
        return team

    async def get_teams(self, org_id: str) -> list[Team]:
        """Get all teams in organization."""
        return await self.teams.find({
            "organization_id": org_id,
        })

    async def update_team(
        self,
        org_id: str,
        team_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Team:
        """Update team."""
        team = await self.get_team(org_id, team_id)

        update_data = {}
        if name:
            # Check new name unique
            existing = await self.teams.find_by_name(org_id, name)
            if existing and existing.id != team_id:
                raise ConflictError(f"Team '{name}' already exists")
            update_data["name"] = name

        if description is not None:
            update_data["description"] = description

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.teams.update(team_id, update_data)
        return await self.teams.read(team_id)

    async def delete_team(self, org_id: str, team_id: str) -> None:
        """Delete team (soft delete)."""
        team = await self.get_team(org_id, team_id)

        await self.teams.update(team_id, {
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "team_deleted",
            resource_id=team_id,
            resource_type="team",
        )
