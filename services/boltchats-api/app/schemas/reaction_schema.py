from pydantic import BaseModel


class ReactionData(BaseModel):
    emoji: str
    users: list[str]


class MessageWithReactions(BaseModel):
    id: str
    room_id: str
    sender_id: str
    content: str
    created_at: str
    edited_at: str | None = None
    deleted_at: str | None = None
    is_deleted: bool = False
    reactions: list[ReactionData] = []
