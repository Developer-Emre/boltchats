from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceMemberSchema(BaseModel):
    user_id: str
    role: str  # owner, admin, member, guest
    joined_at: datetime
    is_active: bool


class WorkspaceSettingsSchema(BaseModel):
    require_email_verification: bool = True
    allow_external_sharing: bool = False
    sso_enabled: bool = False
    message_retention_days: int = 90
    file_retention_days: int = 365
    max_upload_size_mb: int = 100
    default_channel_visibility: str = "public"
    guest_can_post: bool = True
    guest_can_download_files: bool = False


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=256)
    icon_url: str | None = None


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=256)
    icon_url: str | None = None
    settings: WorkspaceSettingsSchema | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    icon_url: str | None
    owner_id: str
    member_count: int
    channel_count: int
    message_count: int
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceDetailResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    icon_url: str | None
    owner_id: str
    members: list[WorkspaceMemberSchema]
    settings: WorkspaceSettingsSchema
    member_count: int
    channel_count: int
    message_count: int
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceResponse]
    next_cursor: str | None = None
