from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.middlewares.workspace_middleware import verify_dm_participant
from app.schemas.message_schema_v2 import (
    CreateMessageRequest,
    EditMessageRequest,
    MessageResponse,
    MessageListResponse,
)
from app.services import message_service_v2

router = APIRouter(
    prefix="/api/v2/workspaces/{workspace_id}/direct-messages/{dm_id}/messages",
    tags=["dm-messages"],
)


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_dm_message(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    payload: CreateMessageRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageResponse:
    """Send a message to a DM group."""
    workspace_id, dm_id = workspace_id_dm
    return await message_service_v2.create_dm(
        workspace_id, dm_id, payload.content, user_id, db
    )


@router.get("", response_model=MessageListResponse)
async def get_dm_messages(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    before: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageListResponse:
    """Get message history for a DM group."""
    workspace_id, dm_id = workspace_id_dm
    return await message_service_v2.get_dm_history(
        workspace_id, dm_id, user_id, db, before=before, limit=limit
    )


@router.patch("/{message_id}", response_model=MessageResponse)
async def edit_dm_message(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    message_id: str = ...,
    payload: EditMessageRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> MessageResponse:
    """Edit a DM message (sender only)."""
    # For DMs, we need to get workspace_id and dm_id, then edit the message
    workspace_id, dm_id = workspace_id_dm
    
    # DM message editing - reuse channel edit logic
    # (messages in DMs are similar structure but with dm_id instead of channel_id)
    return await message_service_v2.edit(
        workspace_id, dm_id, message_id, payload, user_id, db
    )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dm_message(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    message_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Delete a DM message (sender or admin only)."""
    workspace_id, dm_id = workspace_id_dm
    await message_service_v2.delete(workspace_id, dm_id, message_id, user_id, db)
