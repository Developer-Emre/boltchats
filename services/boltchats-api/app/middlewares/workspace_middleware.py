from fastapi import Depends, Path

from app.core.database import get_database
from app.exceptions.http_exceptions import ForbiddenException
from app.middlewares.auth_middleware import get_current_user
from app.services import workspace_service


async def verify_workspace_member(
    workspace_id: str = Path(...),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> str:
    """
    Dependency: Verify user is a member of the workspace.
    Returns workspace_id on success, raises ForbiddenException otherwise.
    """
    await workspace_service.verify_member_access(workspace_id, user_id, db)
    return workspace_id


async def verify_channel_member(
    workspace_id: str = Path(...),
    channel_id: str = Path(...),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> tuple[str, str]:
    """
    Dependency: Verify user is a member of the channel.
    Returns (workspace_id, channel_id) on success.
    """
    from app.services import channel_service

    # First verify workspace access
    await workspace_service.verify_member_access(workspace_id, user_id, db)

    # Then verify channel access
    await channel_service.verify_member_access(workspace_id, channel_id, user_id, db)

    return workspace_id, channel_id


async def verify_dm_participant(
    workspace_id: str = Path(...),
    dm_id: str = Path(...),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> tuple[str, str]:
    """
    Dependency: Verify user is a participant of the DM group.
    Returns (workspace_id, dm_id) on success.
    """
    from app.services import direct_message_service

    # First verify workspace access
    await workspace_service.verify_member_access(workspace_id, user_id, db)

    # Then verify DM access
    await direct_message_service.get_by_id(workspace_id, dm_id, user_id, db)

    return workspace_id, dm_id
