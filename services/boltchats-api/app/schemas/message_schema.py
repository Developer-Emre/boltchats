from datetime import datetime

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    content: str
    created_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    is_deleted: bool = False


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None
