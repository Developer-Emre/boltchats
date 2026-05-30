from datetime import datetime

from pydantic import BaseModel


class QueueMessage(BaseModel):
    """Payload written to the Redis persistence queue for boltchats-storage."""

    room_id: str
    sender_id: str
    content: str
    created_at: datetime


class OutgoingChatMessage(BaseModel):
    """Chat message broadcast to every member of the room."""

    type: str = "message"
    id: str
    room_id: str
    sender_id: str
    content: str
    created_at: str


class MessageConfirmed(BaseModel):
    """Delivery receipt sent *only* to the original sender via direct WS write.

    Never published to the Redis pub/sub channel — other room members never
    see this event. The sender uses it to swap its optimistic placeholder
    (keyed by client_message_id) with the authoritative server id.
    """

    type: str = "message_confirmed"
    client_message_id: str
    server_id: str
