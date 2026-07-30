"""
Identity Domain Repositories

Organizations, Workspaces, Members, Teams, Roles
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import (
    Invitation,
    Member,
    MemberRole,
    Organization,
    RoleDocument,
    Team,
    User,
    Workspace,
)
from app.utils.sparkquark_constants import Collection

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for users"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.USERS.value, User)

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email"""
        return await self.find({"email": email})

    async def find_by_id(self, user_id: str) -> User | None:
        """Find user by ID"""
        return await self.read(user_id)


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for organizations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.ORGANIZATIONS.value, Organization)

    async def find_by_slug(self, slug: str) -> Organization | None:
        """Find organization by slug"""
        return await self.find({"slug": slug})

    async def find_by_owner(self, owner_id: str) -> list[Organization]:
        """Find all organizations owned by user"""
        return await self.find_many({"owner_id": owner_id})

    async def get_active(self, organization_id: str) -> Organization | None:
        """Get organization only if not deleted"""
        return await self.find({
            "_id": organization_id,
            "deleted_at": {"$exists": False}
        })


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for workspaces"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.WORKSPACES.value, Workspace)

    async def find_by_org(self, organization_id: str) -> list[Workspace]:
        """Find all workspaces in organization"""
        return await self.find_many({
            "organization_id": organization_id,
            "deleted_at": {"$exists": False}
        })

    async def find_by_name(self, organization_id: str, name: str) -> Workspace | None:
        """Find workspace by name within organization"""
        return await self.find({
            "organization_id": organization_id,
            "name": name,
            "deleted_at": {"$exists": False}
        })


class MemberRepository(BaseRepository[Member]):
    """Repository for organization members"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.MEMBERS.value, Member)

    async def find_by_user(self, organization_id: str, user_id: str) -> Member | None:
        """Find member in organization"""
        return await self.find({
            "organization_id": organization_id,
            "user_id": user_id
        })

    async def find_by_org(self, organization_id: str, active_only: bool = True) -> list[Member]:
        """Find all members in organization"""
        filter_dict = {"organization_id": organization_id}
        if active_only:
            filter_dict["status"] = "active"
        return await self.find_many(filter_dict)

    async def find_by_team(self, team_id: str) -> list[Member]:
        """Find all members in team"""
        return await self.find_many({"team_ids": team_id})


class MemberRoleRepository(BaseRepository[MemberRole]):
    """Repository for member role assignments"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.MEMBER_ROLES.value, MemberRole)

    async def find_by_member(self, member_id: str) -> list[MemberRole]:
        """Find all roles assigned to member"""
        return await self.find_many({
            "member_id": member_id,
            "expires_at": {"$exists": False}  # Exclude expired roles
        })

    async def find_by_org(self, organization_id: str) -> list[MemberRole]:
        """Find all role assignments in organization"""
        return await self.find_many({"organization_id": organization_id})

    async def has_role(self, member_id: str, role_id: str) -> bool:
        """Check if member has specific role"""
        return await self.exists({
            "member_id": member_id,
            "role_id": role_id,
            "expires_at": {"$exists": False}
        })


class TeamRepository(BaseRepository[Team]):
    """Repository for teams"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.TEAMS.value, Team)

    async def find_by_org(self, organization_id: str) -> list[Team]:
        """Find all teams in organization"""
        return await self.find_many({
            "organization_id": organization_id,
            "deleted_at": {"$exists": False}
        })

    async def find_by_name(self, organization_id: str, name: str) -> Team | None:
        """Find team by name in organization"""
        return await self.find({
            "organization_id": organization_id,
            "name": name,
            "deleted_at": {"$exists": False}
        })


class RoleRepository(BaseRepository[RoleDocument]):
    """Repository for role definitions"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.MEMBER_ROLES.value, RoleDocument)

    async def find_by_name(self, organization_id: str, name: str) -> RoleDocument | None:
        """Find role by name"""
        return await self.find({
            "organization_id": organization_id,
            "name": name
        })

    async def find_by_org(self, organization_id: str) -> list[RoleDocument]:
        """Find all roles in organization"""
        return await self.find_many({"organization_id": organization_id})


class InvitationRepository(BaseRepository[Invitation]):
    """Repository for email invitations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.INVITATIONS.value, Invitation)

    async def find_by_token(self, token: str) -> Invitation | None:
        """Find invitation by token"""
        return await self.find({"token": token})

    async def find_by_email(self, organization_id: str, email: str) -> Invitation | None:
        """Find pending invitation by email"""
        return await self.find({
            "organization_id": organization_id,
            "email": email,
            "accepted_at": {"$exists": False}
        })

    async def find_pending(self, organization_id: str) -> list[Invitation]:
        """Find all pending invitations in organization"""
        from datetime import datetime, timezone
        return await self.find_many({
            "organization_id": organization_id,
            "accepted_at": {"$exists": False},
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
