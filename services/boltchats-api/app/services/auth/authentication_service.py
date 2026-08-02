"""
Authentication Service

User registration and login
"""

from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Member, MemberStatus, User
from app.repositories import MemberRepository, UserRepository
from app.services.base import BaseService, ConflictError, UnauthorizedError

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
        self.token_service = token_service
        self.password_service = PasswordService()

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        org_id: str,
    ) -> dict:
        """
        Register new user and create member in organization.
        
        Args:
            email: User email
            password: Plaintext password
            full_name: User full name
            org_id: Organization to join
            
        Returns:
            {"user_id": "...", "member_id": "..."}
            
        Raises:
            ConflictError: Email already exists
        """
        # Check email not already registered
        existing = await self.users.find_by_email(email)
        if existing:
            raise ConflictError(f"Email {email} already registered")

        # Hash password
        hashed_password = self.password_service.hash_password(password)

        # Create user
        user = User(
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
        )
        user_id = await self.users.create(user)

        # Create member in organization
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
            details={"email": email, "org_id": org_id},
        )

        return {
            "user_id": user_id,
            "member_id": member_id,
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
