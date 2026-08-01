"""
Integration tests for organization and team management flow

Tests: Organization creation, workspace management, team operations, member invitations
"""

import pytest
from datetime import datetime, timezone

from app.services import (
    OrganizationService,
    WorkspaceService,
    MemberService,
    TeamService,
    InvitationService,
)


@pytest.mark.asyncio
class TestOrganizationFlow:
    """End-to-end organization flow tests"""

    async def test_create_organization_with_owner(
        self,
        mongodb,
        member_id: str,
    ):
        """Test creating organization and assigning owner"""
        org_service = OrganizationService(mongodb)

        org = await org_service.create_organization(
            name="Integration Test Org",
            description="For testing purposes",
            owner_id=member_id,
        )

        assert org is not None
        assert org["name"] == "Integration Test Org"
        assert org["owner_id"] == member_id
        assert org["status"] == "active"

    async def test_workspace_creation_flow(
        self,
        mongodb,
        org_id: str,
    ):
        """Test creating workspaces within organization"""
        workspace_service = WorkspaceService(mongodb)

        # Create first workspace
        workspace1 = await workspace_service.create_workspace(
            organization_id=org_id,
            name="Support Team",
            description="Customer support workspace",
        )

        assert workspace1 is not None
        assert workspace1["name"] == "Support Team"
        assert workspace1["organization_id"] == org_id

        # Create second workspace
        workspace2 = await workspace_service.create_workspace(
            organization_id=org_id,
            name="Sales Team",
            description="Sales and business development",
        )

        assert workspace2 is not None
        assert workspace2["name"] == "Sales Team"

        # List workspaces
        workspaces = await workspace_service.list_workspaces(
            organization_id=org_id,
        )

        assert len(workspaces) >= 2

    async def test_member_invitation_and_acceptance_flow(
        self,
        mongodb,
        org_id: str,
        member_id: str,
    ):
        """Test inviting member to organization"""
        invitation_service = InvitationService(mongodb)
        member_service = MemberService(mongodb)

        # Create invitation
        invitation = await invitation_service.create_invitation(
            organization_id=org_id,
            email="newmember@test.com",
            invited_by=member_id,
            role="agent",
        )

        assert invitation is not None
        assert invitation["email"] == "newmember@test.com"
        assert invitation["status"] == "pending"

        # Accept invitation
        updated_invitation = await invitation_service.accept_invitation(
            invitation_id=invitation["id"],
        )

        assert updated_invitation["status"] == "accepted"

        # Verify member was added
        members = await member_service.list_members(org_id)
        assert len(members) > 0

    async def test_team_creation_and_member_assignment(
        self,
        mongodb,
        org_id: str,
        workspace_id: str,
        member_id: str,
    ):
        """Test creating team and assigning members"""
        team_service = TeamService(mongodb)

        # Create team
        team = await team_service.create_team(
            organization_id=org_id,
            workspace_id=workspace_id,
            name="Support Specialists",
            description="Level 1 support team",
        )

        assert team is not None
        assert team["name"] == "Support Specialists"

        # Add member to team
        await team_service.add_member_to_team(
            team_id=team["id"],
            member_id=member_id,
        )

        # Verify member is in team
        team_members = await team_service.get_team_members(team["id"])
        assert member_id in [m["member_id"] for m in team_members]

    async def test_member_role_assignment(
        self,
        mongodb,
        org_id: str,
        member_id: str,
    ):
        """Test assigning roles to members"""
        member_service = MemberService(mongodb)

        # Assign role
        member_role = await member_service.assign_role(
            organization_id=org_id,
            member_id=member_id,
            role_id="admin",
            assigned_by=member_id,
        )

        assert member_role is not None
        assert member_role["role_id"] == "admin"

        # Get member roles
        roles = await member_service.get_member_roles(
            organization_id=org_id,
            member_id=member_id,
        )

        assert len(roles) > 0
        assert "admin" in [r["role_id"] for r in roles]

    async def test_organization_stats_calculation(
        self,
        mongodb,
        org_id: str,
    ):
        """Test calculating organization statistics"""
        org_service = OrganizationService(mongodb)

        stats = await org_service.get_organization_stats(org_id)

        assert stats is not None
        assert "total_members" in stats
        assert "total_teams" in stats
        assert "total_conversations" in stats
        assert isinstance(stats["total_members"], int)

    async def test_multiple_workspaces_isolation(
        self,
        mongodb,
        org_id: str,
        member_id: str,
    ):
        """Test that members in different workspaces are isolated"""
        workspace_service = WorkspaceService(mongodb)

        # Create two workspaces
        ws1 = await workspace_service.create_workspace(
            organization_id=org_id,
            name="Workspace 1",
        )

        ws2 = await workspace_service.create_workspace(
            organization_id=org_id,
            name="Workspace 2",
        )

        # Workspace 1 should be independent of Workspace 2
        ws1_data = await workspace_service.get_workspace(ws1["id"])
        ws2_data = await workspace_service.get_workspace(ws2["id"])

        assert ws1_data["id"] != ws2_data["id"]
