from typing import Literal

from pydantic import BaseModel


class BaseEvent(BaseModel):
    type: str


class JoinRoomEvent(BaseEvent):
    type: Literal["join_room"]
    room_id: str


class LeaveRoomEvent(BaseEvent):
    type: Literal["leave_room"]
    room_id: str


class MessageEvent(BaseEvent):
    type: Literal["message"]
    room_id: str
    content: str


    client_message_id: str | None = None


class MessageEditedEvent(BaseEvent):
    type: Literal["message_edited"]
    room_id: str
    message_id: str
    content: str
    edited_at: str


class MessageDeletedEvent(BaseEvent):
    type: Literal["message_deleted"]
    room_id: str
    message_id: str


class PingEvent(BaseEvent):
    type: Literal["ping"]
