from fastapi import APIRouter, Depends, Query

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.message_schema import MessageListResponse
from app.services import message_service

router = APIRouter(prefix="/rooms", tags=["messages"])


@router.get("/{room_id}/messages", response_model=MessageListResponse)
async def get_messages(
    room_id: str,
    before: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    _current_user: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageListResponse:
    return await message_service.get_history(room_id, db, before=before, limit=limit)
