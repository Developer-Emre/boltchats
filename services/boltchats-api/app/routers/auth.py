from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings as app_settings
from app.core.security import get_current_user as get_current_user_dep
from app.dependencies import get_authentication_service, get_token_service, get_email_service
from app.schemas import (
    CurrentUserResponse,
    HealthResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.base import ConflictError

if TYPE_CHECKING:
    from app.services.auth import AuthenticationService, TokenService
    from app.services.email_service import EmailService

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "boltchats-api",
        "timestamp": datetime.now(timezone.utc),
    }


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
    token_service: "TokenService" = Depends(get_token_service),
    email_service: "EmailService" = Depends(get_email_service),
):
    """Register new user with their own organization"""
    try:
        # Register user and create organization + workspace (Step 1 of Register_flow.md)
        result = await auth_service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
        )
        
        user_id = result["user_id"]
        
        # Step 2: Generate email verification token
        verification_token = await token_service.create_email_verification_token(
            user_id=user_id,
            email=payload.email,
        )
        
        # Step 3: Send verification email
        await email_service.send_verification_email(
            to=payload.email,
            name=payload.full_name,
            token=verification_token,
            frontend_url=app_settings.frontend_url,
        )
        
        return RegisterResponse(
            user_id=user_id,
            email=payload.email,
            verification_token=verification_token,  # For development only
            verification_link=f"{app_settings.frontend_url}/verify-email?token={verification_token}",
        )
    
    except ConflictError as e:
        await logger.aerror("register_failed", error=str(e), email=payload.email)
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


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
):
    """Verify user email (Step 2 of Register_flow.md)"""
    try:
        result = await auth_service.verify_email(payload.token)
        return VerifyEmailResponse(
            user_id=result["user_id"],
            email=result["email"],
            verified=result["verified"],
        )
    except Exception as e:
        await logger.aerror("verify_email_failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email verification failed",
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
    """Refresh access token (with token rotation)"""
    try:
        result = await auth_service.refresh_access_token(payload.refresh_token)

        # ⭐ Return NEW refresh token (rotation)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],  # NEW token
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
    auth_service: "AuthenticationService" = Depends(get_authentication_service),
):
    """Get current authenticated user info"""
    try:
        # Fetch user from DB to get email/full_name
        user = await auth_service.users.read(current_user["user_id"])
        
        return CurrentUserResponse(
            user_id=current_user["user_id"],
            email=user.email if user else "",
            full_name=user.full_name if user else "",
            organization_id=current_user["org_id"],
            workspace_id="",  # TODO: Add workspace_id to token when multi-workspace is implemented
            member_id=current_user["member_id"],
            roles=current_user["roles"],
            permissions=[],  # TODO: Implement permission resolution from roles
        )
    except Exception as e:
        await logger.aerror("get_me_failed", error=str(e), user_id=current_user.get("user_id"))
        # Return partial info on error (don't fail the request)
        return CurrentUserResponse(
            user_id=current_user["user_id"],
            email="",
            full_name="",
            organization_id=current_user["org_id"],
            workspace_id="",
            member_id=current_user["member_id"],
            roles=current_user["roles"],
            permissions=[],
        )
