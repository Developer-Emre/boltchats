"""
Organization Service

Organization management, members, teams, roles, invitations
"""

from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import (
    Invitation,
    Member,
    MemberRole,
    MemberStatus,
    Organization,
    RoleDocument,
    Team,
    Workspace,
)
from app.repositories import (
    InvitationRepository,
    MemberRepository,
    MemberRoleRepository,
    OrganizationRepository,
    RoleRepository,
    TeamRepository,
    WorkspaceRepository,
)

from .base import (
    BaseService,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)


class OrganizationService(BaseService):
    """Organization and team management service"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.organizations = OrganizationRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.members = MemberRepository(db)
        self.member_roles = MemberRoleRepository(db)
        self.teams = TeamRepository(db)
        self.roles = RoleRepository(db)
        self.invitations = InvitationRepository(db)

    # ─── ORGANIZATION ─────────────────────────────────────────────────

    async def get_organization(self, org_id: str) -> Organization:
        """Get organization details."""
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

    # ─── WORKSPACE ────────────────────────────────────────────────────

    async def create_workspace(
        self,
        org_id: str,
        name: str,
        description: str = "",
    ) -> Workspace:
        """Create workspace in organization."""
        # Check org exists
        await self.get_organization(org_id)

        # Check workspace name unique in org
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
            details={"organization_id": org_id, "name": name},
        )

        return await self.workspaces.read(workspace_id)

    # ─── MEMBERS ──────────────────────────────────────────────────────

    async def get_members(self, org_id: str) -> list[Member]:
        """Get all active members in organization."""
        return await self.members.find_by_org(org_id, active_only=True)

    async def add_member(
        self,
        org_id: str,
        user_id: str,
        role_id: str,
        assigned_by: str,
    ) -> Member:
        """Add member to organization with role."""
        # Check org exists
        await self.get_organization(org_id)

        # Check member doesn't already exist
        existing = await self.members.find_by_user(org_id, user_id)
        if existing:
            raise ConflictError(f"User {user_id} already member of organization")

        # Create member
        member = Member(
            organization_id=org_id,
            user_id=user_id,
            status=MemberStatus.ACTIVE,
            team_ids=[],
        )
        member_id = await self.members.create(member)

        # Assign role
        member_role = MemberRole(
            organization_id=org_id,
            member_id=member_id,
            role_id=role_id,
            assigned_by=assigned_by,
        )
        await self.member_roles.create(member_role)

        await self.log_action(
            "member_added",
            resource_id=member_id,
            resource_type="member",
            details={"organization_id": org_id, "role_id": role_id},
        )

        return await self.members.read(member_id)

    async def remove_member(self, org_id: str, member_id: str) -> None:
        """Remove member from organization."""
        # Check member exists
        member = await self.members.read(member_id)
        if not member or member.organization_id != org_id:
            raise NotFoundError("Member", member_id)

        # Soft delete
        await self.members.update(member_id, {
            "status": MemberStatus.INACTIVE,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "member_removed",
            resource_id=member_id,
            resource_type="member",
        )

    # ─── MEMBER ROLES ─────────────────────────────────────────────────

    async def assign_role(
        self,
        org_id: str,
        member_id: str,
        role_id: str,
        assigned_by: str,
        expires_at: datetime | None = None,
    ) -> MemberRole:
        """Assign role to member."""
        # Check member exists in org
        member = await self.members.read(member_id)
        if not member or member.organization_id != org_id:
            raise NotFoundError("Member", member_id)

        # Check role exists in org
        role = await self.roles.find({
            "organization_id": org_id,
            "id": role_id,
        })
        if not role:
            raise NotFoundError("Role", role_id)

        # Check member doesn't already have role
        has_role = await self.member_roles.has_role(member_id, role_id)
        if has_role:
            raise ConflictError(f"Member already has role {role_id}")

        # Create role assignment
        member_role = MemberRole(
            organization_id=org_id,
            member_id=member_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at,
        )
        role_id = await self.member_roles.create(member_role)

        await self.log_action(
            "role_assigned",
            resource_id=role_id,
            resource_type="member_role",
        )

        return await self.member_roles.read(role_id)

    async def remove_role(self, org_id: str, member_id: str, role_id: str) -> None:
        """Remove role from member."""
        # Find assignment
        assignment = await self.member_roles.find({
            "member_id": member_id,
            "role_id": role_id,
        })
        if not assignment:
            raise NotFoundError("MemberRole", f"{member_id}:{role_id}")

        # Delete assignment
        await self.member_roles.delete(assignment.id)

        await self.log_action(
            "role_removed",
            resource_id=assignment.id,
            resource_type="member_role",
        )

    # ─── TEAMS ────────────────────────────────────────────────────────

    async def create_team(
        self,
        org_id: str,
        name: str,
        description: str = "",
    ) -> Team:
        """Create team in organization."""
        # Check org exists
        await self.get_organization(org_id)

        # Check team name unique in org
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
        )

        return await self.teams.read(team_id)

    async def add_member_to_team(
        self,
        org_id: str,
        team_id: str,
        member_id: str,
    ) -> None:
        """Add member to team."""
        # Check team exists in org
        team = await self.teams.read(team_id)
        if not team or team.organization_id != org_id:
            raise NotFoundError("Team", team_id)

        # Check member exists in org
        member = await self.members.read(member_id)
        if not member or member.organization_id != org_id:
            raise NotFoundError("Member", member_id)

        # Add team to member's teams
        if team_id not in member.team_ids:
            member.team_ids.append(team_id)
            await self.members.update(member_id, {
                "team_ids": member.team_ids,
                "updated_at": datetime.now(timezone.utc),
            })

        await self.log_action(
            "member_added_to_team",
            resource_id=member_id,
            resource_type="member",
            details={"team_id": team_id},
        )

    # ─── INVITATIONS ──────────────────────────────────────────────────

    async def invite_member(
        self,
        org_id: str,
        email: str,
        role_id: str,
        invited_by: str,
    ) -> Invitation:
        """Send invitation to join organization."""
        # Check org exists
        await self.get_organization(org_id)

        # Check no pending invitation
        existing = await self.invitations.find_by_email(org_id, email)
        if existing:
            raise ConflictError(f"Pending invitation already sent to {email}")

        # Generate token
        import secrets
        token = secrets.token_urlsafe(32)

        # Create invitation
        invitation = Invitation(
            organization_id=org_id,
            email=email,
            role_id=role_id,
            token=token,
            invited_by=invited_by,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        inv_id = await self.invitations.create(invitation)

        await self.log_action(
            "invitation_sent",
            resource_id=inv_id,
            resource_type="invitation",
            details={"email": email},
        )

        return await self.invitations.read(inv_id)

    async def accept_invitation(
        self,
        token: str,
        user_id: str,
    ) -> tuple[str, str]:
        """Accept invitation to join organization.
        
        Returns:
            (organization_id, member_id)
        """
        # Find invitation
        invitation = await self.invitations.find_by_token(token)
        if not invitation:
            raise NotFoundError("Invitation", token)

        # Check not expired
        if invitation.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Invitation has expired")

        # Check not already accepted
        if invitation.accepted_at:
            raise ValidationError("Invitation already accepted")

        # Accept invitation
        await self.invitations.update(invitation.id, {
            "accepted_at": datetime.now(timezone.utc),
        })

        # Add user to organization with role
        member = await self.add_member(
            invitation.organization_id,
            user_id,
            invitation.role_id,
            invitation.invited_by,
        )

        await self.log_action(
            "invitation_accepted",
            resource_id=invitation.id,
            resource_type="invitation",
            details={"member_id": member.id},
        )

        return invitation.organization_id, member.id
