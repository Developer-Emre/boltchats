"""
Authentication Service

Login, register, token management, password hashing
"""

from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import create_token
from app.models.identity import Member, MemberStatus, Organization
from app.repositories import (
    InvitationRepository,
    MemberRepository,
    OrganizationRepository,
)

from .base import BaseService, ConflictError, InvalidTokenError, NotFoundError, UnauthorizedError

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(BaseService):
    """Authentication and authorization service"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.members = MemberRepository(db)
        self.organizations = OrganizationRepository(db)
        self.invitations = InvitationRepository(db)

    async def register(
        self,
        email: EmailStr,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> dict:
        """Register new user with organization.
        
        Args:
            email: User email
            password: Password (will be hashed)
            full_name: User's full name
            organization_name: Organization name
            
        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "organization_id": str,
                "user_id": str,
            }
        """
        # Check if member exists with this email
        existing = await self.members.find({
            "email": email
        })
        if existing:
            raise ConflictError(f"User with email {email} already exists")

        # Hash password
        hashed_password = pwd_context.hash(password)

        # Create organization
        org = Organization(
            name=organization_name,
            slug=organization_name.lower().replace(" ", "-"),
            owner_id=email,  # Use email as temp user_id
            settings={"language": "en", "timezone": "UTC"},
        )
        org_id = await self.organizations.create(org)

        # Create member (organization owner)
        member = Member(
            organization_id=org_id,
            user_id=email,
            status=MemberStatus.ACTIVE,
            team_ids=[],
        )
        member_id = await self.members.create(member)

        # Store password hash in Redis (temporary, will be moved to Users collection)
        from app.core.redis import get_redis
        redis = get_redis()
        await redis.hset(f"user:{email}", "password_hash", hashed_password)
        await redis.hset(f"user:{email}", "member_id", member_id)
        await redis.hset(f"user:{email}", "organization_id", org_id)

        # Generate tokens
        access_token = create_token(
            data={"sub": email, "org_id": org_id, "member_id": member_id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_token(
            data={"sub": email, "org_id": org_id, "type": "refresh"},
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        )

        # Store refresh token in Redis
        await redis.setex(
            f"refresh_token:{email}",
            settings.refresh_token_expire_days * 86400,
            refresh_token,
        )

        await self.log_action("user_registered", resource_id=email, details={
            "organization_id": org_id,
            "member_id": member_id,
        })

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "organization_id": org_id,
            "user_id": member_id,
        }

    async def login(
        self,
        email: EmailStr,
        password: str,
    ) -> dict:
        """Login with email and password.
        
        Args:
            email: User email
            password: Password
            
        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "organization_id": str,
                "user_id": str,
            }
        """
        from app.core.redis import get_redis
        redis = get_redis()

        # Get password hash from Redis
        password_hash = await redis.hget(f"user:{email}", "password_hash")
        if not password_hash:
            raise UnauthorizedError("Invalid email or password")

        # Verify password
        if not pwd_context.verify(password, password_hash):
            raise UnauthorizedError("Invalid email or password")

        # Get member info
        member_id = await redis.hget(f"user:{email}", "member_id")
        org_id = await redis.hget(f"user:{email}", "organization_id")

        if not member_id or not org_id:
            raise NotFoundError("User", email)

        # Generate tokens
        access_token = create_token(
            data={"sub": email, "org_id": org_id, "member_id": member_id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        refresh_token = create_token(
            data={"sub": email, "org_id": org_id, "type": "refresh"},
            expires_delta=timedelta(days=settings.refresh_token_expire_days),
        )

        # Store refresh token
        await redis.setex(
            f"refresh_token:{email}",
            settings.refresh_token_expire_days * 86400,
            refresh_token,
        )

        await self.log_action("user_login", resource_id=email)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "organization_id": str(org_id),
            "user_id": str(member_id),
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            {
                "access_token": str,
            }
        """
        from app.core.security import verify_token
        from app.core.redis import get_redis
        
        redis = get_redis()

        # Verify refresh token
        try:
            payload = verify_token(refresh_token)
        except Exception:
            raise InvalidTokenError()

        email = payload.get("sub")
        org_id = payload.get("org_id")
        token_type = payload.get("type")

        if token_type != "refresh":
            raise InvalidTokenError()

        # Check token in Redis
        stored_token = await redis.get(f"refresh_token:{email}")
        if stored_token != refresh_token:
            raise InvalidTokenError()

        # Get member info
        member_id = await redis.hget(f"user:{email}", "member_id")

        # Generate new access token
        new_access_token = create_token(
            data={"sub": email, "org_id": org_id, "member_id": member_id},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return {
            "access_token": new_access_token,
        }

    async def logout(self, email: EmailStr) -> None:
        """Logout user.
        
        Args:
            email: User email
        """
        from app.core.redis import get_redis
        redis = get_redis()

        # Delete refresh token
        await redis.delete(f"refresh_token:{email}")

        await self.log_action("user_logout", resource_id=email)

    def hash_password(self, password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
