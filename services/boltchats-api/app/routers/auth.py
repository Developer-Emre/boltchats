from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_authentication_service, get_token_service
from app.schemas import (
    CurrentUserResponse,
    HealthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import (
    AuthenticationService,
    TokenService,
)

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
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    """Register new user and organization"""
    try:
        tokens = await auth_service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
        )

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    """Login user"""
    try:
        tokens = await auth_service.login(
            email=payload.email,
            password=payload.password,
        )

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service),
):
    """Refresh access token"""
    try:
        tokens = await token_service.refresh_token(payload.refresh_token)

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    token_service: TokenService = Depends(get_token_service),
):
    """Logout user (revoke refresh token)"""
    try:
        if payload.refresh_token:
            await token_service.revoke_token(payload.refresh_token)

        return {"status": "logged_out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user(
    current_user = Depends(get_current_user),
):
    """Get current authenticated user info"""
    return CurrentUserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        organization_id=current_user["organization_id"],
        workspace_id=current_user["workspace_id"],
        member_id=current_user["member_id"],
        roles=current_user["roles"],
        permissions=current_user["permissions"],
    )
