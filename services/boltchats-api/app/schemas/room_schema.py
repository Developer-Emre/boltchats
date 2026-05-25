from datetime import datetime

from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=256)
    is_private: bool = False


class RoomResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    member_ids: list[str]
    is_private: bool
    created_at: datetime


class RoomListResponse(BaseModel):
    items: list[RoomResponse]
    next_cursor: str | None
