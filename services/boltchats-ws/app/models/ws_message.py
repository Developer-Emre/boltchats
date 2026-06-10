from datetime import datetime

from pydantic import BaseModel


class QueueMessage(BaseModel):
    """Payload written to the Redis persistence queue for boltchats-storage."""

    id: str
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


class MessageEditedBroadcast(BaseModel):
    """Broadcast to all room members when a message is edited."""

    type: str = "message_edited"
    room_id: str
    message_id: str
    content: str
    edited_at: str


class MessageDeletedBroadcast(BaseModel):
    """Broadcast to all room members when a message is deleted."""

    type: str = "message_deleted"
    room_id: str
    message_id: str
    deleted_at: str


class ReactionAddedBroadcast(BaseModel):
    """Broadcast to all room members when a reaction is added."""

    type: str = "reaction_added"
    room_id: str
    message_id: str
    emoji: str
    user_id: str


class ReactionRemovedBroadcast(BaseModel):
    """Broadcast to all room members when a reaction is removed."""

    type: str = "reaction_removed"
    room_id: str
    message_id: str
    emoji: str
    user_id: str
