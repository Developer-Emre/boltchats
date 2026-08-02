from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user as get_current_user_dep
from app.dependencies import get_authentication_service, get_token_service
from app.schemas import (
    CurrentUserResponse,
    HealthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.base import ConflictError

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "boltchats-api",
        "timestamp": datetime.now(timezone.utc),
    }


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
    token_service: "TokenService" = Depends(get_token_service),
):
    """Register new user with their own organization"""
    try:
        # Register user and create organization
        result = await auth_service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
        )
        
        # Create tokens
        tokens = await token_service.create_tokens(
            user_id=result["user_id"],
            org_id=result["organization_id"],
            member_id=result["member_id"],
            roles=[],
        )
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            user_id=result["user_id"],
            member_id=result["member_id"],
            organization_id=result["organization_id"],
        )
    
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        await logger.aerror("register_failed", error=str(e), email=payload.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
):
    """Login user"""
    try:
        result = await auth_service.login(
            email=payload.email,
            password=payload.password,
        )

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result.get("expires_in", 1800),
            user_id=result.get("user_id"),
            member_id=result.get("member_id"),
            organization_id=result.get("org_id"),
        )

    except Exception as e:
        await logger.aerror("login_failed", error=str(e), email=payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
):
    """Refresh access token"""
    try:
        result = await auth_service.refresh_access_token(payload.refresh_token)

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=payload.refresh_token,
            expires_in=result.get("expires_in", 1800),
            member_id=result.get("member_id"),
            organization_id=result.get("org_id"),
        )

    except Exception as e:
        await logger.aerror("refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user_dep),
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
):
    """Logout user (revoke refresh token)"""
    try:
        user_id = current_user["user_id"]
        await auth_service.logout(user_id)
        return {"status": "logged_out"}

    except Exception as e:
        await logger.aerror("logout_failed", error=str(e), user_id=current_user.get("user_id"))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed",
        )


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user = Depends(get_current_user_dep),
):
    """Get current authenticated user info"""
    return CurrentUserResponse(
        user_id=current_user["user_id"],
        email="",  # Not in token, would need DB lookup
        full_name="",  # Not in token, would need DB lookup
        organization_id=current_user["org_id"],
        workspace_id="",  # Not in token
        member_id=current_user["member_id"],
        roles=current_user["roles"],
        permissions=[],  # Would need permission service
    )
