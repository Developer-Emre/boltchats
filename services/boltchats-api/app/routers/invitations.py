from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_database
from app.middlewares.auth_middleware import get_current_user
from app.schemas.invitation_schema import (
    CreateInvitationRequest,
    AcceptInvitationRequest,
    InvitationResponse,
    InvitationListResponse,
)
from app.services import invitation_service, workspace_service

router = APIRouter(prefix="/api/v2/invitations", tags=["invitations"])


@router.post(
    "/workspaces/{workspace_id}",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    workspace_id: str,
    payload: CreateInvitationRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> InvitationResponse:
    """Create an invitation to workspace (admin/owner only)."""
    # Verify user has access to workspace
    await workspace_service.verify_member_access(workspace_id, user_id, db)
    # TODO: Verify user is admin/owner
    return await invitation_service.create(workspace_id, payload, user_id, db)


@router.get("/workspaces/{workspace_id}", response_model=InvitationListResponse)
async def list_workspace_invitations(
    workspace_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> InvitationListResponse:
    """List all pending invitations for workspace (admin/owner only)."""
    # Verify user has access to workspace
    await workspace_service.verify_member_access(workspace_id, user_id, db)
    # TODO: Verify user is admin/owner
    return await invitation_service.list_by_workspace(
        workspace_id, db, cursor=cursor, limit=limit
    )


@router.post("/accept", response_model=InvitationResponse)
async def accept_invitation(
    payload: AcceptInvitationRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> InvitationResponse:
    """Accept an invitation using code."""
    return await invitation_service.accept(payload.code, user_id, db)


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_database),
) -> None:
    """Revoke an invitation (admin/owner only)."""
    # TODO: Verify workspace membership and admin/owner role
    await invitation_service.revoke(invitation_id, user_id, db)
