from datetime import datetime, timezone

from pydantic import BaseModel, Field


class InvitationDocument(BaseModel):
    """Represents a workspace invitation."""

    id: str | None = Field(default=None, alias="_id")
    workspace_id: str
    
    # Who invited
    invited_by: str
    
    # Who to invite
    invited_email: str | None = None  # If not registered yet
    invited_user_id: str | None = None  # If already registered
    
    # Invitation details
    role: str = "member"  # member, admin, guest
    
    # Invitation code (for link-based invites)
    code: str  # unique, e.g. "invite_abc123xyz"
    code_expires_at: datetime
    
    # Status
    status: str = "pending"  # pending, accepted, declined, revoked
    accepted_at: datetime | None = None
    accepted_by: str | None = None
    declined_at: datetime | None = None
    revoked_at: datetime | None = None
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
