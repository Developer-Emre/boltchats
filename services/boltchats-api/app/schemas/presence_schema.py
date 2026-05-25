from pydantic import BaseModel


class RoomPresenceResponse(BaseModel):
    room_id: str
    online_user_ids: list[str]
    count: int


class UserPresenceResponse(BaseModel):
    user_id: str
    is_online: bool


class OnlineUsersResponse(BaseModel):
    online_user_ids: list[str]
    count: int
