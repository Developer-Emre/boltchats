from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.message_schema import EditMessageRequest, MessageListResponse, MessageResponse
from app.services import message_service

router = APIRouter(prefix="/rooms", tags=["messages"])


@router.get("/{room_id}/messages", response_model=MessageListResponse)
async def get_messages(
    room_id: str,
    before: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageListResponse:
    return await message_service.get_history(room_id, current_user, db, before=before, limit=limit)


@router.patch("/{room_id}/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    room_id: str,
    message_id: str,
    payload: EditMessageRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageResponse:
    return await message_service.edit_message(room_id, message_id, current_user, payload, db)


@router.delete("/{room_id}/messages/{message_id}", status_code=204)
async def delete_message(
    room_id: str,
    message_id: str,
    current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    await message_service.delete_message(room_id, message_id, current_user, db)
