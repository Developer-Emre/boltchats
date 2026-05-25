from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.middlewares.auth_middleware import get_current_user
from app.schemas.presence_schema import (
    OnlineUsersResponse,
    RoomPresenceResponse,
    UserPresenceResponse,
)
from app.services import presence_service

router = APIRouter(prefix="/presence", tags=["presence"])


@router.get("/rooms/{room_id}", response_model=RoomPresenceResponse)
async def get_room_presence(
    room_id: str,
    _current_user: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> RoomPresenceResponse:
    return await presence_service.get_room_presence(room_id, redis)


@router.get("/users/{user_id}", response_model=UserPresenceResponse)
async def get_user_presence(
    user_id: str,
    _current_user: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> UserPresenceResponse:
    return await presence_service.get_user_presence(user_id, redis)


@router.get("/online", response_model=OnlineUsersResponse)
async def get_online_users(
    _current_user: str = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> OnlineUsersResponse:
    return await presence_service.get_online_users(redis)
