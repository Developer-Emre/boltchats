from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: str
    content: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None
