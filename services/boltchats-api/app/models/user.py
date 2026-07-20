from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field


class UserWorkspace(BaseModel):
    """Represents user's membership in a workspace."""

    workspace_id: str
    role: str  # owner, admin, member, guest
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    is_active: bool = True


class UserStatus(BaseModel):
    """User status information."""

    state: str = "offline"  # active, away, offline, dnd (do not disturb)
    status_emoji: str = ""
    status_text: str = ""
    status_expires_at: datetime | None = None


class UserPreferences(BaseModel):
    """User preferences."""

    theme: str = "auto"  # light, dark, auto
    notifications: str = "all"  # all, mentions, none
    language: str = "en"
    timezone: str = "UTC"


class UserDocument(BaseModel):
    """Represents a user document as stored in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    username: str
    email: str
    display_name: str = ""
    hashed_password: str
    avatar_url: str | None = None
    bio: str = ""

    # Workspaces this user is part of (global)
    workspaces: list[UserWorkspace] = Field(default_factory=list)

    # Account status
    is_active: bool = True
    is_email_verified: bool = False
    email_verification_token: str | None = None
    email_verification_expires_at: datetime | None = None

    # User status (current)
    status: UserStatus = Field(default_factory=UserStatus)

    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    # OAuth connections
    connected_accounts: dict = Field(default_factory=dict)

    # Security
    two_factor_enabled: bool = False
    two_factor_secret: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
