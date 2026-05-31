from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis

from app.core.database import get_database
from app.core.redis import get_redis
from app.schemas.auth_schema import (
    AccessTokenResponse,
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UserInfo,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=AuthResponse)
async def google_login(
    payload: GoogleAuthRequest,
    db=Depends(get_database),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    return await auth_service.google_login(payload, db, redis)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db=Depends(get_database),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    return await auth_service.register(payload, db, redis)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    db=Depends(get_database),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    return await auth_service.login(payload, db, redis)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    payload: RefreshRequest,
    redis: Redis = Depends(get_redis),
) -> AccessTokenResponse:
    return await auth_service.refresh(payload, redis)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    redis: Redis = Depends(get_redis),
) -> None:
    await auth_service.logout(payload, redis)
