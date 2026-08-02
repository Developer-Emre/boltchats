"""
Authentication Service

User registration and login
"""

from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Member, MemberStatus, Organization, User
from app.repositories import MemberRepository, OrganizationRepository, UserRepository
from app.services.base import BaseService, ConflictError, UnauthorizedError
from app.utils.helpers import generate_slug

from .password_service import PasswordService
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
        self.organizations = OrganizationRepository(db)
        self.token_service = token_service
        self.password_service = PasswordService()

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> dict:
        """
        Register new user with their own organization (multi-tenant).
        
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
                "organization_name": "..."
            }
            
        Raises:
            ConflictError: Email already exists or organization slug taken
        """
        # Check email not already registered
        existing = await self.users.find_by_email(email)
        if existing:
            raise ConflictError(f"Email {email} already registered")

        # Generate slug from organization name
        slug = generate_slug(organization_name)
        
        # Check slug not already taken
        existing_org = await self.organizations.find_by_slug(slug)
        if existing_org:
            raise ConflictError(f"Organization '{organization_name}' already exists")

        # Hash password
        hashed_password = self.password_service.hash_password(password)

        # Create user
        user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
        )
        user_id = await self.users.create(user)

        # Create organization (user is owner)
        organization = Organization(
            name=organization_name,
            slug=slug,
            owner_id=user_id,
        )
        org_id = await self.organizations.create(organization)

        # Create member in organization (owner as member)
        member = Member(
            organization_id=org_id,
            user_id=user_id,
            status=MemberStatus.ACTIVE,
            team_ids=[],
        )
        member_id = await self.members.create(member)

        await self.log_action(
            "user_registered",
            resource_id=user_id,
            resource_type="user",
            details={
                "email": email,
                "organization_name": organization_name,
                "org_id": org_id,
            },
        )

        return {
            "user_id": user_id,
            "member_id": member_id,
            "organization_id": org_id,
            "organization_name": organization_name,
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