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


class PingEvent(BaseEvent):
    type: Literal["ping"]
