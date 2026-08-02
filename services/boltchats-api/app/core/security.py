from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from starlette.requests import Request
from jose import jwt, JWTError

from app.core.config import settings


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError on failure."""
    try:
        # TokenService uses jwt_secret_key, must match
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
    except JWTError as e:
        raise ValueError(f"Token validation failed: {e}")


# Security schemes
security = HTTPBearer()


async def get_current_user(request: Request) -> dict:
    """Extract and validate current user from bearer token.
    
    Returns dict with: user_id, org_id, member_id, roles, type, iat, exp
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
        
        payload = decode_token(token)
        
        # Verify it's an access token (not refresh)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Invalid token: missing user_id")
        
        return payload  # Return full payload dict
        
    except (ValueError, JWTError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )