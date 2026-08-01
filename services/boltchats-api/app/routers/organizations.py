"""
Organizations Router

Endpoints for organizations, workspaces, teams, members, roles, invitations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.dependencies import (
    get_organization_service,
    get_workspace_service,
    get_member_service,
    get_team_service,
    get_role_service,
    get_invitation_service,
    get_permission_service,
)
from app.schemas import (
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationResponse,
    MemberCreateRequest,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    PermissionResponse,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
    TeamCreateRequest,
    TeamResponse,
    TeamUpdateRequest,
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services import (
    InvitationService,
    MemberService,
    OrganizationService,
    PermissionService,
    RoleService,
    TeamService,
    WorkspaceService,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


# Organization endpoints
@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateRequest,
    service: OrganizationService = Depends(get_organization_service),
):
    """Create organization"""
    try:
        org = await service.create_organization(**payload.dict())
        return org
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
):
    """Get organization"""
    org = await service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdateRequest,
    current_user = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
):
    """Update organization"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        org = await service.update_organization(org_id, payload.dict(exclude_none=True))
        return org
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Workspace endpoints
@router.post("/{org_id}/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    org_id: str,
    payload: WorkspaceCreateRequest,
    current_user = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Create workspace"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        workspace = await service.create_workspace(org_id, **payload.dict())
        return workspace
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    org_id: str,
    workspace_id: str,
    current_user = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get workspace"""
    workspace = await service.get_workspace(org_id, workspace_id)
    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return workspace


@router.patch("/{org_id}/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    org_id: str,
    workspace_id: str,
    payload: WorkspaceUpdateRequest,
    current_user = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Update workspace"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        workspace = await service.update_workspace(
            org_id, workspace_id, payload.dict(exclude_none=True)
        )
        return workspace
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Member endpoints
@router.post("/{org_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    org_id: str,
    payload: MemberCreateRequest,
    current_user = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
):
    """Add member to organization"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        member = await service.add_member(
            org_id,
            workspace_id=current_user["workspace_id"],
            **payload.dict(),
        )
        return member
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}/members", response_model=MemberListResponse)
async def list_members(
    org_id: str,
    current_user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MemberService = Depends(get_member_service),
):
    """List members in organization"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    members = await service.list_members(
        org_id, limit=limit, offset=offset
    )
    return {
        "items": members,
        "total": len(members),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{org_id}/members/{member_id}", response_model=MemberResponse)
async def get_member(
    org_id: str,
    member_id: str,
    current_user = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
):
    """Get member"""
    member = await service.get_member(org_id, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return member


@router.patch("/{org_id}/members/{member_id}", response_model=MemberResponse)
async def update_member(
    org_id: str,
    member_id: str,
    payload: MemberUpdateRequest,
    current_user = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
):
    """Update member"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        member = await service.update_member(
            org_id, member_id, payload.dict(exclude_none=True)
        )
        return member
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Team endpoints
@router.post("/{org_id}/workspaces/{workspace_id}/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    org_id: str,
    workspace_id: str,
    payload: TeamCreateRequest,
    current_user = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
):
    """Create team"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        team = await service.create_team(org_id, workspace_id, **payload.dict())
        return team
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Role endpoints
@router.post("/{org_id}/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    org_id: str,
    payload: RoleCreateRequest,
    current_user = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
):
    """Create custom role"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        role = await service.create_role(org_id, **payload.dict())
        return role
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{org_id}/roles", response_model=list[RoleResponse])
async def list_roles(
    org_id: str,
    current_user = Depends(get_current_user),
    service: RoleService = Depends(get_role_service),
):
    """List roles"""
    roles = await service.list_roles(org_id)
    return roles


# Invitation endpoints
@router.post("/{org_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def send_invitation(
    org_id: str,
    payload: InvitationCreateRequest,
    current_user = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
):
    """Send invitation to join organization"""
    if org_id != current_user["organization_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    try:
        invitation = await service.send_invitation(
            org_id,
            workspace_id=current_user["workspace_id"],
            **payload.dict(),
        )
        return invitation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/{token}/accept", response_model=MemberResponse)
async def accept_invitation(
    token: str,
    payload: InvitationAcceptRequest,
    service: InvitationService = Depends(get_invitation_service),
):
    """Accept invitation"""
    try:
        member = await service.accept_invitation(token, payload.password)
        return member
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
