from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MessageMention(BaseModel):
    """Message mentions information."""

    user_ids: list[str] = Field(default_factory=list)
    is_channel_mention: bool = False
    is_here_mention: bool = False
    is_everyone_mention: bool = False


class MessageAttachment(BaseModel):
    """Message attachment."""

    type: str  # file, link, code_snippet
    file_id: str | None = None
    name: str | None = None
    url: str | None = None
    mime_type: str | None = None


class MessageDocument(BaseModel):
    """Represents a message document."""

    id: str | None = Field(default=None, alias="_id")
    
    # Workspace & Channel
    workspace_id: str
    channel_id: str | None = None  # For public/private channels
    dm_id: str | None = None  # For direct messages
    
    # Legacy (for migration)
    room_id: str | None = None
    
    # Content
    sender_id: str
    content: str
    
    # Threading
    thread_id: str | None = None  # If reply to message
    is_thread_parent: bool = False
    thread_reply_count: int = 0
    thread_participants: list[str] = Field(default_factory=list)
    
    # Mentions
    mentions: MessageMention = Field(default_factory=MessageMention)
    
    # Attachments
    attachments: list[MessageAttachment] = Field(default_factory=list)
    
    # Reactions
    reactions: dict[str, list[str]] = Field(default_factory=dict)
    
    # Edit history
    edited_at: datetime | None = None
    edited_by: str | None = None
    edit_history: list[dict] = Field(default_factory=list)
    
    # Soft delete
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    
    # Pinned
    is_pinned: bool = False
    pinned_at: datetime | None = None
    pinned_by: str | None = None
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
