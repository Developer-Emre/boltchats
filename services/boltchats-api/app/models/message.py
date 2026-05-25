from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MessageDocument(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    room_id: str
    sender_id: str
    content: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
