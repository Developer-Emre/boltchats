"""
Member Service

Organization membership management
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Member, MemberStatus
from app.repositories import MemberRepository, OrganizationRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class MemberService(BaseService):
    """Manage members in organization"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.members = MemberRepository(db)
        self.organizations = OrganizationRepository(db)

    async def add_member(
        self,
        org_id: str,
        user_id: str,
    ) -> Member:
        """
        Add member to organization.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            
        Returns:
            Member
        """
        # Check org exists
        org = await self.organizations.get_active(org_id)
        if not org:
            raise NotFoundError("Organization", org_id)

        # Check member doesn't already exist
        existing = await self.members.find_by_user(org_id, user_id)
        if existing:
            raise ConflictError(f"User already member of organization")

        # Create member
        member = Member(
            organization_id=org_id,
            user_id=user_id,
            status=MemberStatus.ACTIVE,
            team_ids=[],
        )
        member_id = await self.members.create(member)

        await self.log_action(
            "member_added",
            resource_id=member_id,
            resource_type="member",
        )

        return await self.members.read(member_id)

    async def get_member(self, org_id: str, member_id: str) -> Member:
        """Get member."""
        member = await self.members.read(member_id)
        if not member or member.organization_id != org_id:
            raise NotFoundError("Member", member_id)
        return member

    async def get_members(self, org_id: str) -> list[Member]:
        """Get all active members in organization."""
        return await self.members.find_by_org(org_id, active_only=True)

    async def remove_member(self, org_id: str, member_id: str) -> None:
        """Remove member from organization (soft delete)."""
        member = await self.get_member(org_id, member_id)

        await self.members.update(member_id, {
            "status": MemberStatus.INACTIVE,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "member_removed",
            resource_id=member_id,
            resource_type="member",
        )

    async def add_member_to_team(
        self,
        org_id: str,
        member_id: str,
        team_id: str,
    ) -> Member:
        """Add member to team."""
        member = await self.get_member(org_id, member_id)

        if team_id not in member.team_ids:
            member.team_ids.append(team_id)
            await self.members.update(member_id, {
                "team_ids": member.team_ids,
                "updated_at": datetime.now(timezone.utc),
            })

        return await self.members.read(member_id)

    async def remove_member_from_team(
        self,
        org_id: str,
        member_id: str,
        team_id: str,
    ) -> Member:
        """Remove member from team."""
        member = await self.get_member(org_id, member_id)

        if team_id in member.team_ids:
            member.team_ids.remove(team_id)
            await self.members.update(member_id, {
                "team_ids": member.team_ids,
                "updated_at": datetime.now(timezone.utc),
            })

        return await self.members.read(member_id)

    async def update_member_status(
        self,
        org_id: str,
        member_id: str,
        status: MemberStatus,
    ) -> Member:
        """Update member status."""
        member = await self.get_member(org_id, member_id)

        await self.members.update(member_id, {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        })

        return await self.members.read(member_id)
