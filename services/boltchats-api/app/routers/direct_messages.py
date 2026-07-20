from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.middlewares.workspace_middleware import (
    verify_workspace_member,
    verify_dm_participant,
)
from app.schemas.direct_message_schema import (
    CreateDirectMessageRequest,
    DirectMessageResponse,
    DirectMessageDetailResponse,
    DirectMessageListResponse,
)
from app.services import direct_message_service

router = APIRouter(
    prefix="/api/v2/workspaces/{workspace_id}/direct-messages",
    tags=["direct-messages"],
)


@router.post("", response_model=DirectMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_direct_message(
    workspace_id: str = Depends(verify_workspace_member),
    payload: CreateDirectMessageRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> DirectMessageResponse:
    """Create a new direct message group."""
    return await direct_message_service.create(workspace_id, payload, user_id, db)


@router.get("", response_model=DirectMessageListResponse)
async def list_direct_messages(
    workspace_id: str = Depends(verify_workspace_member),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> DirectMessageListResponse:
    """List all DM groups for current user."""
    return await direct_message_service.list_by_user(
        workspace_id, user_id, db, cursor=cursor, limit=limit
    )


@router.get("/{dm_id}", response_model=DirectMessageDetailResponse)
async def get_direct_message(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> DirectMessageDetailResponse:
    """Get direct message group details."""
    workspace_id, dm_id = workspace_id_dm
    return await direct_message_service.get_detail(workspace_id, dm_id, user_id, db)


@router.post("/{dm_id}/participants/{participant_id}", response_model=DirectMessageResponse)
async def add_participant(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    participant_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> DirectMessageResponse:
    """Add a participant to DM group."""
    workspace_id, dm_id = workspace_id_dm
    return await direct_message_service.add_participant(
        workspace_id, dm_id, participant_id, user_id, db
    )


@router.delete(
    "/{dm_id}/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_participant(
    workspace_id_dm: tuple[str, str] = Depends(verify_dm_participant),
    participant_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Remove a participant from DM group."""
    workspace_id, dm_id = workspace_id_dm
    await direct_message_service.remove_participant(
        workspace_id, dm_id, participant_id, user_id, db
    )
