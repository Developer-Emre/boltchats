"""
Token Service

JWT token generation, validation, and refresh token management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
import redis.asyncio as redis

from app.core.config import Settings
from app.utils.constants import REDIS_PREFIX_REFRESH_TOKEN


class TokenService:
    """Handle JWT tokens and refresh token storage"""

    def __init__(self, redis_client: redis.Redis, settings: Settings):
        self.redis = redis_client
        self.settings = settings

    async def create_tokens(
        self,
        user_id: str,
        org_id: str,
        member_id: str,
        roles: list[str],
    ) -> dict[str, str]:
        """
        Create access token (short-lived) and refresh token (long-lived).
        
        Args:
            user_id: User ID
            org_id: Organization ID
            member_id: Member ID in organization
            roles: List of role IDs
            
        Returns:
            {"access_token": "...", "refresh_token": "..."}
        """
        now = datetime.now(timezone.utc)

        # Access token: 15 minutes
        access_payload = {
            "user_id": user_id,
            "org_id": org_id,
            "member_id": member_id,
            "roles": roles,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        }
        access_token = jwt.encode(
            access_payload,
            self.settings.jwt_secret_key,
            algorithm="HS256",
        )

        # Refresh token: 7 days
        refresh_payload = {
            "user_id": user_id,
            "org_id": org_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=7),
        }
        refresh_token = jwt.encode(
            refresh_payload,
            self.settings.jwt_secret_key,
            algorithm="HS256",
        )

        # Store refresh token in Redis for revocation
        refresh_key = f"{REDIS_PREFIX_REFRESH_TOKEN}:{user_id}"
        await self.redis.setex(
            refresh_key,
            7 * 24 * 3600,  # 7 days in seconds
            refresh_token,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def verify_access_token(self, token: str) -> dict:
        """
        Verify and decode access token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload dict
            
        Raises:
            jwt.InvalidTokenError: If invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=["HS256"],
            )
            
            # Check token type
            if payload.get("type") != "access":
                raise jwt.InvalidTokenError("Not an access token")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token expired")
        except jwt.InvalidTokenError:
            raise

    async def verify_refresh_token(self, token: str) -> dict:
        """
        Verify and decode refresh token.
        
        Also checks Redis for revocation.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload dict
            
        Raises:
            jwt.InvalidTokenError: If invalid/expired/revoked
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=["HS256"],
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")
            
            # Check not revoked (should still be in Redis)
            user_id = payload.get("user_id")
            refresh_key = f"{REDIS_PREFIX_REFRESH_TOKEN}:{user_id}"
            stored_token = await self.redis.get(refresh_key)
            
            if not stored_token or stored_token.decode() != token:
                raise jwt.InvalidTokenError("Token revoked")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token expired")
        except jwt.InvalidTokenError:
            raise

    async def revoke_refresh_token(self, user_id: str) -> None:
        """
        Revoke refresh token (logout).
        
        Args:
            user_id: User ID
        """
        refresh_key = f"{REDIS_PREFIX_REFRESH_TOKEN}:{user_id}"
        await self.redis.delete(refresh_key)

    async def create_access_token_from_refresh(
        self,
        refresh_token: str,
        roles: list[str],
    ) -> str:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            roles: List of role IDs
            
        Returns:
            New access token
        """
        payload = await self.verify_refresh_token(refresh_token)
        
        user_id = payload["user_id"]
        org_id = payload["org_id"]
        member_id = payload.get("member_id")
        
        now = datetime.now(timezone.utc)
        access_payload = {
            "user_id": user_id,
            "org_id": org_id,
            "member_id": member_id,
            "roles": roles,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        }
        
        access_token = jwt.encode(
            access_payload,
            self.settings.jwt_secret_key,
            algorithm="HS256",
        )
        
        return access_token
