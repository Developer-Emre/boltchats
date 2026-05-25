from datetime import datetime

from pydantic import BaseModel


class QueueMessage(BaseModel):
    """Payload written to the Redis persistence queue for boltchats-storage."""

    room_id: str
    sender_id: str
    content: str
    created_at: datetime


class OutgoingChatMessage(BaseModel):
    """Chat message payload delivered to WebSocket clients."""

    type: str = "message"
    id: str
    room_id: str
    sender_id: str
    content: str
    created_at: str
