"""
Request/Response schemas for Organization domain
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.identity import MemberStatus, RoleEnum


class OrganizationCreateRequest(BaseModel):
    """Create organization request"""
    name: str = Field(..., min_length=1)
    slug: Optional[str] = None


class OrganizationUpdateRequest(BaseModel):
    """Update organization request"""
    name: Optional[str] = None
    slug: Optional[str] = None


class OrganizationResponse(BaseModel):
    """Organization response"""
    id: str
    name: str
    slug: str
    member_count: int
    workspace_count: int
    created_at: datetime


class WorkspaceCreateRequest(BaseModel):
    """Create workspace request"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    """Update workspace request"""
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Workspace response"""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    member_count: int
    team_count: int
    created_at: datetime


class MemberCreateRequest(BaseModel):
    """Add member to workspace"""
    user_id: str
    role: RoleEnum = RoleEnum.AGENT


class MemberUpdateRequest(BaseModel):
    """Update member request"""
    status: Optional[MemberStatus] = None
    role: Optional[RoleEnum] = None


class MemberRoleResponse(BaseModel):
    """Member role assignment"""
    id: str
    member_id: str
    role_id: str
    assigned_at: datetime
    assigned_by: Optional[str]
    expires_at: Optional[datetime]


class MemberResponse(BaseModel):
    """Member response"""
    id: str
    organization_id: str
    workspace_id: str
    user_id: str
    email: str
    full_name: str
    status: MemberStatus
    roles: list[MemberRoleResponse]
    team_ids: list[str]
    created_at: datetime


class TeamCreateRequest(BaseModel):
    """Create team request"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class TeamUpdateRequest(BaseModel):
    """Update team request"""
    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(BaseModel):
    """Team response"""
    id: str
    workspace_id: str
    name: str
    description: Optional[str]
    member_count: int
    created_at: datetime


class PermissionResponse(BaseModel):
    """Permission response"""
    code: str
    name: str
    description: Optional[str]


class RoleCreateRequest(BaseModel):
    """Create custom role request"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    permissions: list[str]


class RoleUpdateRequest(BaseModel):
    """Update role request"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[list[str]] = None


class RoleResponse(BaseModel):
    """Role response"""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    is_system_role: bool
    permissions: list[PermissionResponse]
    created_at: datetime


class InvitationCreateRequest(BaseModel):
    """Send invitation request"""
    email: EmailStr
    role: RoleEnum = RoleEnum.AGENT
    message: Optional[str] = None


class InvitationAcceptRequest(BaseModel):
    """Accept invitation request"""
    token: str
    password: Optional[str] = None  # If creating new account


class InvitationResponse(BaseModel):
    """Invitation response"""
    id: str
    organization_id: str
    workspace_id: str
    email: str
    role: RoleEnum
    status: str  # pending, accepted, expired
    token: Optional[str]  # Only in list, not detail
    created_at: datetime
    expires_at: datetime


class MemberListResponse(BaseModel):
    """Paginated member list"""
    items: list[MemberResponse]
    total: int
    limit: int
    offset: int
