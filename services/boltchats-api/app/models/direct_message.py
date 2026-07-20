from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DirectMessageDocument(BaseModel):
    """Represents a direct message conversation."""

    id: str | None = Field(default=None, alias="_id")
    workspace_id: str
    
    type: str = "direct_message"
    
    # Participants (for 1-to-1 or group DMs)
    participants: list[str]
    
    # Who created this DM
    created_by: str
    
    # Read status
    read_status: dict[str, dict] = Field(default_factory=dict)
    # Example: { "user_1": {"read_at": timestamp, "read_message_id": "msg_123"} }
    
    # Last activity
    last_message_at: datetime | None = None
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
