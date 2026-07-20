from datetime import datetime

from pydantic import BaseModel, Field


class CreateDirectMessageRequest(BaseModel):
    participant_ids: list[str] = Field(min_items=1, max_items=100)
    name: str | None = Field(default=None, max_length=64)


class DirectMessageResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    participants: list[str]
    participant_count: int
    created_by: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DirectMessageDetailResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    participants: list[str]
    participant_count: int
    created_by: str
    is_archived: bool
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DirectMessageListResponse(BaseModel):
    items: list[DirectMessageResponse]
    next_cursor: str | None = None
