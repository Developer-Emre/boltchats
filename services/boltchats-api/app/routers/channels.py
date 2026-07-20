from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.channel_schema import (
    CreateChannelRequest,
    UpdateChannelRequest,
    ChannelResponse,
    ChannelDetailResponse,
    ChannelListResponse,
)
from app.services import channel_service, workspace_service

router = APIRouter(
    prefix="/api/v2/workspaces/{workspace_id}/channels",
    tags=["channels"],
)


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    workspace_id: str,
    payload: CreateChannelRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelResponse:
    """Create a new channel in workspace."""
    # Verify user has access to workspace
    await workspace_service.verify_member_access(workspace_id, user_id, db)
    return await channel_service.create(workspace_id, payload, user_id, db)


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    workspace_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelListResponse:
    """List all channels in workspace."""
    # Verify user has access to workspace
    await workspace_service.verify_member_access(workspace_id, user_id, db)
    return await channel_service.list_by_workspace(workspace_id, db, cursor=cursor, limit=limit)


@router.get("/{channel_id}", response_model=ChannelDetailResponse)
async def get_channel(
    workspace_id: str,
    channel_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelDetailResponse:
    """Get channel details."""
    # Verify user has access to channel
    await channel_service.verify_member_access(workspace_id, channel_id, user_id, db)
    return await channel_service.get_detail(workspace_id, channel_id, db)


@router.patch("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    workspace_id: str,
    channel_id: str,
    payload: UpdateChannelRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelResponse:
    """Update channel (owner only)."""
    # Verify user has access to channel
    await channel_service.verify_member_access(workspace_id, channel_id, user_id, db)
    return await channel_service.update(workspace_id, channel_id, payload, user_id, db)


@router.post("/{channel_id}/members/{member_id}", response_model=ChannelResponse)
async def add_channel_member(
    workspace_id: str,
    channel_id: str,
    member_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelResponse:
    """Add a member to channel."""
    # Verify user has access to channel
    await channel_service.verify_member_access(workspace_id, channel_id, user_id, db)
    # TODO: Verify user is admin/owner
    return await channel_service.add_member(workspace_id, channel_id, member_id, user_id, db)


@router.delete("/{channel_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel_member(
    workspace_id: str,
    channel_id: str,
    member_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Remove a member from channel."""
    # Verify user has access to channel
    await channel_service.verify_member_access(workspace_id, channel_id, user_id, db)
    # TODO: Verify user is admin/owner
    await channel_service.remove_member(workspace_id, channel_id, member_id, user_id, db)


@router.post("/{channel_id}/archive", response_model=ChannelResponse)
async def archive_channel(
    workspace_id: str,
    channel_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> ChannelResponse:
    """Archive channel (owner only)."""
    return await channel_service.archive(workspace_id, channel_id, user_id, db)
