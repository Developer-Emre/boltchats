"""
Authentication Service

User registration and login
"""

from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Member, MemberRole, MemberStatus, Organization, User, Workspace
from app.repositories import (
    MemberRepository,
    MemberRoleRepository,
    OrganizationRepository,
    UserRepository,
    WorkspaceRepository,
)
from app.services.base import BaseService, ConflictError, UnauthorizedError
from app.services.conversation.label_service import LabelService
from app.utils.helpers import generate_slug

from .password_service import PasswordService
from .role_service import RoleService
from .token_service import TokenService


class AuthenticationService(BaseService):
    """Handle user registration and login"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: redis.Redis,
        token_service: TokenService,
    ):
        super().__init__(db)
        self.users = UserRepository(db)
        self.members = MemberRepository(db)
        self.member_roles = MemberRoleRepository(db)
        self.organizations = OrganizationRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.token_service = token_service
        self.password_service = PasswordService()
        self.role_service = RoleService(db)
        self.label_service = LabelService(db)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> dict:
        """
        Register new user with their own organization (multi-tenant).
        Follows Business_workflow.md flow:
        
        1. Owner Registers
        2. Organization Created
        3. Workspace Created (default)
        4. Member created (Owner role by default)
        
        Args:
            email: User email
            password: Plaintext password
            full_name: User full name
            organization_name: Name for the new organization
            
        Returns:
            {
                "user_id": "...",
                "member_id": "...",
                "organization_id": "...",
                "organization_name": "...",
                "workspace_id": "..."
            }
            
        Raises:
            ConflictError: Email already exists or organization slug taken
        """
        # Step 1: Validate email not already registered (global constraint)
        existing = await self.users.find_by_email(email)
        if existing:
            raise ConflictError(f"Email {email} already registered")

        # Step 2: Generate slug and check uniqueness (org names must be unique)
        slug = generate_slug(organization_name)
        existing_org = await self.organizations.find_by_slug(slug)
        if existing_org:
            raise ConflictError(f"Organization '{organization_name}' already exists")

        # Step 3: Hash password
        hashed_password = self.password_service.hash_password(password)

        # Step 4: Create User
        user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
        )
        user_id = await self.users.create(user)

        # Step 5: Create Organization (owner is the new user)
        organization = Organization(
            name=organization_name,
            slug=slug,
            owner_id=user_id,
        )
        org_id = await self.organizations.create(organization)

        # Step 6: Create Default Workspace
        # Every organization starts with at least one workspace
        default_workspace = Workspace(
            organization_id=org_id,
            name="Support",  # Default workspace name
            slug="support",
            description="Default support workspace",
        )
        workspace_id = await self.workspaces.create(default_workspace)

        # Step 7: Seed Default Roles (Admin, Manager, Agent, Viewer)
        # Follows Register_flow.md Step 5
        role_ids = await self.role_service.seed_default_roles(org_id)
        admin_role_id = role_ids["admin_role_id"]

        # Step 8: Seed System Labels (New, Waiting, Urgent, VIP, Spam, Resolved)
        # Follows Register_flow.md Step 7
        await self.label_service.seed_default_labels(org_id)

        # Step 9: Create Member (Owner gets added as ACTIVE member)
        member = Member(
            organization_id=org_id,
            user_id=user_id,
            status=MemberStatus.ACTIVE,
            team_ids=[],
        )
        member_id = await self.members.create(member)

        # Step 10: Assign Admin role to owner
        # Without this, owner has zero permissions in their own organization
        owner_role_assignment = MemberRole(
            organization_id=org_id,
            member_id=member_id,
            role_id=admin_role_id,
            assigned_by=user_id,  # self-assigned at org creation
        )
        await self.member_roles.create(owner_role_assignment)

        # Step 11: Audit log
        await self.log_action(
            "user_registered",
            resource_id=user_id,
            resource_type="user",
            details={
                "email": email,
                "organization_name": organization_name,
                "org_id": org_id,
                "workspace_id": workspace_id,
                "admin_role_id": admin_role_id,
            },
        )

        # Step 12: Return all created resources
        return {
            "user_id": user_id,
            "member_id": member_id,
            "organization_id": org_id,
            "organization_name": organization_name,
            "workspace_id": workspace_id,
            "role_ids": [admin_role_id],
        }

    async def verify_email(self, token: str) -> dict:
        """
        Verify user email using verification token.
        
        Follows Register_flow.md Step 2.
        
        Args:
            token: Email verification token
            
        Returns:
            {"user_id": "...", "email": "...", "verified": true}
            
        Raises:
            UnauthorizedError: Invalid/expired token
        """
        from jose import jwt as jose_jwt
        
        try:
            payload = await self.token_service.verify_email_token(token)
        except jose_jwt.JWTError as e:
            raise UnauthorizedError(f"Invalid verification token: {str(e)}")
        
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        # Verify user exists before updating
        user = await self.users.read(user_id)
        if not user:
            raise UnauthorizedError("User not found")
        
        # Update user to mark email as verified
        update_result = await self.users.update(
            user_id,
            {
                "email_verified": True,
                "email_verified_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        
        if not update_result:
            raise UnauthorizedError("Failed to update email verification status")
        
        # Invalidate the verification token
        await self.token_service.invalidate_email_verification_token(user_id)
        
        return {
            "user_id": user_id,
            "email": email,
            "verified": True,
        }

    async def login(
        self,
        email: str,
        password: str,
    ) -> dict:
        # Find user
        user = await self.users.find_by_email(email)
        if not user:
            raise UnauthorizedError("Invalid email or password")

        # Verify email (Step 2 of Register_flow.md)
        if not user.email_verified:
            raise UnauthorizedError("Email not verified. Please check your inbox for verification link.")

        # Verify password (constant-time comparison)
        if not self.password_service.verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        # Find active members (user may be in multiple organizations)
        members = await self.members.find_many({"user_id": user.id})
        if not members:
            raise UnauthorizedError("User has no organization membership")

        # Filter for active members only
        active_members = [m for m in members if m.status == MemberStatus.ACTIVE]
        if not active_members:
            raise UnauthorizedError("No active organization membership")

        # Get primary member (first active)
        member = active_members[0]
        org_id = member.organization_id

        # Get roles for member
        from app.repositories import MemberRoleRepository
        role_repo = MemberRoleRepository(self.db)
        member_roles = await role_repo.find_many({
            "member_id": member.id,
        })
        role_ids = [mr.role_id for mr in (member_roles or [])]

        # Create tokens
        tokens = await self.token_service.create_tokens(
            user_id=user.id,
            org_id=org_id,
            member_id=member.id,
            roles=role_ids,
        )

        await self.log_action(
            "user_login",
            resource_id=user.id,
            resource_type="user",
            details={"email": email},
        )

        return {
            "user_id": user.id,
            "member_id": member.id,
            "org_id": org_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens.get("expires_in", 900),
            "role_ids": role_ids,
        }

    async def logout(self, user_id: str) -> None:
        """
        Logout user (revoke refresh token).
        
        Args:
            user_id: User ID
        """
        await self.token_service.revoke_refresh_token(user_id)

        await self.log_action(
            "user_logout",
            resource_id=user_id,
            resource_type="user",
        )

    async def get_active_member(self, user_id: str) -> Optional[Member]:
        """
        Get active member for user (primary organization membership).
        
        Used to restore member_id during token refresh.
        
        Args:
            user_id: User ID
            
        Returns:
            First active Member or None
        """
        members = await self.members.find_many({"user_id": user_id})
        if not members:
            return None
        
        active_members = [m for m in members if m.status == MemberStatus.ACTIVE]
        return active_members[0] if active_members else None

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Verify refresh token, re-fetch current member/roles from DB,
        and issue a fresh access token.

        Returns:
            {"access_token": "...", "expires_in": 1800}

        Raises:
            UnauthorizedError: Invalid/expired/revoked refresh token,
                or no active membership.
        """
        from jose import jwt as jose_jwt  # for exception type only

        try:
            payload = await self.token_service.verify_refresh_token(refresh_token)
        except jose_jwt.JWTError:
            raise UnauthorizedError("Invalid refresh token")

        user_id = payload["user_id"]

        # Re-fetch active membership + roles from DB (don't trust stale token data)
        members = await self.members.find_many({"user_id": user_id})
        active_members = [m for m in members if m.status == MemberStatus.ACTIVE]
        if not active_members:
            raise UnauthorizedError("No active organization membership")

        member = active_members[0]
        org_id = member.organization_id

        from app.repositories import MemberRoleRepository
        role_repo = MemberRoleRepository(self.db)
        member_roles = await role_repo.find_many({"member_id": member.id})
        role_ids = [mr.role_id for mr in (member_roles or [])]

        tokens = await self.token_service.create_access_token(
            user_id=user_id,
            org_id=org_id,
            member_id=member.id,
            roles=role_ids,
        )

        # Include member_id and org_id in response (for refresh endpoint)
        return {
            **tokens,
            "member_id": member.id,
            "org_id": org_id,
        }