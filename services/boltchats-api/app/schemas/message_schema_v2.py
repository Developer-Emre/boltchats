from datetime import datetime

from pydantic import BaseModel, Field


class CreateMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: str
    workspace_id: str
    channel_id: str | None = None
    dm_id: str | None = None
    sender_id: str
    content: str
    created_at: datetime
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None = None
