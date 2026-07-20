from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.middlewares.workspace_middleware import verify_channel_member
from app.schemas.message_schema_v2 import (
    CreateMessageRequest,
    EditMessageRequest,
    MessageResponse,
    MessageListResponse,
)
from app.services import message_service_v2

router = APIRouter(
    prefix="/api/v2/workspaces/{workspace_id}/channels/{channel_id}/messages",
    tags=["channel-messages"],
)


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_message(
    workspace_id_channel: tuple[str, str] = Depends(verify_channel_member),
    payload: CreateMessageRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageResponse:
    """Send a message to a channel."""
    workspace_id, channel_id = workspace_id_channel
    return await message_service_v2.create(workspace_id, channel_id, payload.content, user_id, db)


@router.get("", response_model=MessageListResponse)
async def get_channel_messages(
    workspace_id_channel: tuple[str, str] = Depends(verify_channel_member),
    before: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageListResponse:
    """Get message history for a channel."""
    workspace_id, channel_id = workspace_id_channel
    return await message_service_v2.get_history(
        workspace_id, channel_id, user_id, db, before=before, limit=limit
    )


@router.patch("/{message_id}", response_model=MessageResponse)
async def edit_channel_message(
    workspace_id_channel: tuple[str, str] = Depends(verify_channel_member),
    message_id: str = ...,
    payload: EditMessageRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageResponse:
    """Edit a channel message (sender only)."""
    workspace_id, channel_id = workspace_id_channel
    return await message_service_v2.edit(
        workspace_id, channel_id, message_id, payload, user_id, db
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_message(
    workspace_id_channel: tuple[str, str] = Depends(verify_channel_member),
    message_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Delete a channel message (sender or admin only)."""
    workspace_id, channel_id = workspace_id_channel
    await message_service_v2.delete(workspace_id, channel_id, message_id, user_id, db)
