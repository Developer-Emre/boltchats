"""
Token Service

JWT token generation, validation, and refresh token management
"""

from datetime import datetime, timedelta, timezone

from jose import jwt
import redis.asyncio as redis

from app.core.config import Settings
from app.utils.constants import REDIS_PREFIX_REFRESH_TOKEN

# Email verification token prefix for Redis
REDIS_PREFIX_EMAIL_VERIFICATION = "email_verification"


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
    ) -> dict[str, str | int]:
        """
        Create access token (short-lived) and refresh token (long-lived).
        
        Args:
            user_id: User ID
            org_id: Organization ID
            member_id: Member ID in organization
            roles: List of role IDs
            
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 1800  # Access token lifetime in seconds
            }
        """
        now = datetime.now(timezone.utc)
        
        # Calculate expiry times from settings
        access_expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        refresh_expires_delta = timedelta(days=self.settings.refresh_token_expire_days)

        # Access token payload
        access_payload = {
            "user_id": user_id,
            "org_id": org_id,
            "member_id": member_id,
            "roles": roles,
            "type": "access",
            "iat": now,
            "exp": now + access_expires_delta,
        }
        access_token = jwt.encode(
            access_payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.algorithm,
        )

        # Refresh token payload
        refresh_payload = {
            "user_id": user_id,
            "org_id": org_id,
            "type": "refresh",
            "iat": now,
            "exp": now + refresh_expires_delta,
        }
        refresh_token = jwt.encode(
            refresh_payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.algorithm,
        )

        # Store refresh token in Redis for revocation
        refresh_key = f"{REDIS_PREFIX_REFRESH_TOKEN}:{user_id}"
        refresh_ttl_seconds = int(refresh_expires_delta.total_seconds())
        await self.redis.setex(
            refresh_key,
            refresh_ttl_seconds,
            refresh_token,
        )

        # Calculate expires_in in seconds for client
        expires_in_seconds = int(access_expires_delta.total_seconds())

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": expires_in_seconds,
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
                algorithms=[self.settings.algorithm],
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
                algorithms=[self.settings.algorithm],
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")
            
            # Check not revoked (should still be in Redis)
            user_id = payload.get("user_id")
            refresh_key = f"{REDIS_PREFIX_REFRESH_TOKEN}:{user_id}"
            stored_token = await self.redis.get(refresh_key)
            
            if not stored_token:
                raise jwt.InvalidTokenError("Token revoked")
            
            # Decode stored_token if it's bytes
            stored_token_str = stored_token.decode() if isinstance(stored_token, bytes) else stored_token
            if stored_token_str != token:
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

    async def create_access_token(
            self,   
            user_id: str,
            org_id: str,
            member_id: str,
            roles: list[str],
        ) -> dict[str, str | int]:
            """
            Create a new access token from already-known identity data.
            Used after refresh-token verification, once member_id/roles
            have been re-fetched from the DB by the caller.
            """
            now = datetime.now(timezone.utc)
            access_expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)

            access_payload = {
                "user_id": user_id,
                "org_id": org_id,
                "member_id": member_id,
                "roles": roles,
                "type": "access",
                "iat": now,
                "exp": now + access_expires_delta,
            }
            access_token = jwt.encode(
                access_payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.algorithm,
            )

            return {
                "access_token": access_token,
                "expires_in": int(access_expires_delta.total_seconds()),
            }

    async def create_email_verification_token(self, user_id: str, email: str) -> str:
        """
        Create email verification token (stored in Redis, not JWT).
        
        Args:
            user_id: User ID
            email: User email
            
        Returns:
            Verification token
        """
        now = datetime.now(timezone.utc)
        expires_delta = timedelta(minutes=self.settings.email_verification_token_expire_minutes)
        
        token_payload = {
            "user_id": user_id,
            "email": email,
            "type": "email_verification",
            "iat": now,
            "exp": now + expires_delta,
        }
        
        token = jwt.encode(
            token_payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.algorithm,
        )
        
        # Store in Redis for quick lookup
        verify_key = f"{REDIS_PREFIX_EMAIL_VERIFICATION}:{user_id}"
        ttl_seconds = int(expires_delta.total_seconds())
        await self.redis.setex(verify_key, ttl_seconds, token)
        
        return token
    
    async def verify_email_token(self, token: str) -> dict:
        """
        Verify email verification token.
        
        Args:
            token: Verification token
            
        Returns:
            Token payload dict with user_id and email
            
        Raises:
            jwt.InvalidTokenError: If invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.algorithm],
            )
            
            if payload.get("type") != "email_verification":
                raise jwt.InvalidTokenError("Not an email verification token")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Verification token expired")
        except jwt.InvalidTokenError:
            raise
    
    async def invalidate_email_verification_token(self, user_id: str) -> None:
        """
        Invalidate email verification token after successful verification.
        
        Args:
            user_id: User ID
        """
        verify_key = f"{REDIS_PREFIX_EMAIL_VERIFICATION}:{user_id}"
        await self.redis.delete(verify_key)

