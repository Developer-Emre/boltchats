from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.room_schema import CreateRoomRequest, RoomListResponse, RoomResponse
from app.services import room_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: CreateRoomRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> RoomResponse:
    return await room_service.create(payload, user_id, db)


@router.get("", response_model=RoomListResponse)
async def list_rooms(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> RoomListResponse:
    return await room_service.list_rooms(db, cursor=cursor, limit=limit)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    _current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> RoomResponse:
    return await room_service.get_by_id(room_id, db)


@router.post("/{room_id}/join", response_model=RoomResponse)
async def join_room(
    room_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> RoomResponse:
    return await room_service.join(room_id, user_id, db)


@router.delete("/{room_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_room(
    room_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    await room_service.leave(room_id, user_id, db)
