from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT_MESSAGE = "direct_message"
    SHARED_CHANNEL = "shared_channel"


class ChannelSettings(BaseModel):
    can_post: list[str] = Field(default_factory=lambda: ["member"])
    can_invite: list[str] = Field(default_factory=lambda: ["admin"])
    thread_replies_allowed: bool = True
    auto_join_new_members: bool = True
    posting_restrictions: str = "none"  # none, mods, owner


class ChannelDocument(BaseModel):
    """Represents a channel document (evolved from Room)."""

    id: str | None = Field(default=None, alias="_id")
    workspace_id: str
    name: str
    display_name: str = ""
    description: str = ""
    
    type: ChannelType = ChannelType.PUBLIC
    topic: str = ""
    purpose: str = ""
    
    owner_id: str
    members: list[str] = Field(default_factory=list)
    
    settings: ChannelSettings = Field(default_factory=ChannelSettings)
    
    # Archive status
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by: str | None = None
    
    # Default channel (auto-created)
    is_default: bool = False
    
    # Stats
    message_count: int = 0
    member_count: int = 0
    last_message_at: datetime | None = None
    
    # Shared channels (future feature)
    shared_workspaces: list[str] = Field(default_factory=list)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
