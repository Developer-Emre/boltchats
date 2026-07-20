from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.middlewares.workspace_middleware import verify_workspace_member
from app.schemas.workspace_schema import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    WorkspaceResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
)
from app.services import workspace_service

router = APIRouter(prefix="/api/v2/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: CreateWorkspaceRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> WorkspaceResponse:
    """Create a new workspace."""
    return await workspace_service.create(payload, user_id, db)


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> WorkspaceListResponse:
    """List all workspaces for the current user."""
    return await workspace_service.list_by_user(user_id, db, cursor=cursor, limit=limit)


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
async def get_workspace(
    workspace_id: str = Depends(verify_workspace_member),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> WorkspaceDetailResponse:
    """Get workspace details by ID."""
    return await workspace_service.get_detail(workspace_id, db)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str = Depends(verify_workspace_member),
    payload: UpdateWorkspaceRequest = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> WorkspaceResponse:
    """Update workspace (owner only)."""
    return await workspace_service.update(workspace_id, payload, user_id, db)


@router.post("/{workspace_id}/members/{member_id}", response_model=WorkspaceResponse)
async def add_workspace_member(
    workspace_id: str = Depends(verify_workspace_member),
    member_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> WorkspaceResponse:
    """Add a member to workspace (admin/owner only)."""
    # TODO: Verify user is admin/owner
    return await workspace_service.add_member(workspace_id, member_id, user_id, db)


@router.delete(
    "/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workspace_member(
    workspace_id: str = Depends(verify_workspace_member),
    member_id: str = ...,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Remove a member from workspace (admin/owner only)."""
    # TODO: Verify user is admin/owner
    await workspace_service.remove_member(workspace_id, member_id, user_id, db)
