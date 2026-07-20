from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class WorkspaceSettings(BaseModel):
    """Workspace configuration settings."""

    require_email_verification: bool = True
    allow_external_sharing: bool = False
    sso_enabled: bool = False
    message_retention_days: int = 90
    file_retention_days: int = 365
    max_upload_size_mb: int = 100
    default_channel_visibility: str = "public"  # public or private
    guest_can_post: bool = True
    guest_can_download_files: bool = False


class WorkspaceMember(BaseModel):
    """Represents a member in a workspace."""

    user_id: str
    role: str  # owner, admin, member, guest
    joined_at: datetime
    is_active: bool = True


class WorkspaceBilling(BaseModel):
    """Billing information for workspace."""

    plan: str = "free"  # free, pro, enterprise
    billing_email: str | None = None
    billing_cycle_start: datetime | None = None
    billing_cycle_end: datetime | None = None


class WorkspaceDocument(BaseModel):
    """Represents a workspace document as stored in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    name: str
    slug: str  # unique, URL-safe (tech-corp)
    description: str = ""
    icon_url: str | None = None

    owner_id: str
    members: list[WorkspaceMember] = Field(default_factory=list)

    settings: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    billing: WorkspaceBilling = Field(default_factory=WorkspaceBilling)

    # Stats
    member_count: int = 0
    channel_count: int = 0
    message_count: int = 0

    # Status
    is_active: bool = True
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
