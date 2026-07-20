from typing import Literal

from pydantic import BaseModel


class BaseEvent(BaseModel):
    type: str


# Legacy room-based events (v1) - kept for backward compatibility
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
    deleted_at: str


class PingEvent(BaseEvent):
    type: Literal["ping"]


class ReactionAddedEvent(BaseEvent):
    type: Literal["reaction_added"]
    room_id: str
    message_id: str
    emoji: str
    user_id: str


class ReactionRemovedEvent(BaseEvent):
    type: Literal["reaction_removed"]
    room_id: str
    message_id: str
    emoji: str
    user_id: str


# New workspace/channel events (v2)
class JoinWorkspaceEvent(BaseEvent):
    type: Literal["workspace.join"]
    workspace_id: str


class LeaveWorkspaceEvent(BaseEvent):
    type: Literal["workspace.leave"]
    workspace_id: str


class JoinChannelEvent(BaseEvent):
    type: Literal["channel.join"]
    workspace_id: str
    channel_id: str


class LeaveChannelEvent(BaseEvent):
    type: Literal["channel.leave"]
    workspace_id: str
    channel_id: str


class ChannelMessageEvent(BaseEvent):
    type: Literal["channel.message"]
    workspace_id: str
    channel_id: str
    content: str
    client_message_id: str | None = None


class ChannelMessageEditedEvent(BaseEvent):
    type: Literal["channel.message.edited"]
    workspace_id: str
    channel_id: str
    message_id: str
    content: str
    edited_at: str


class ChannelMessageDeletedEvent(BaseEvent):
    type: Literal["channel.message.deleted"]
    workspace_id: str
    channel_id: str
    message_id: str
    deleted_at: str


class DMMessageEvent(BaseEvent):
    type: Literal["dm.message"]
    workspace_id: str
    dm_id: str
    content: str
    client_message_id: str | None = None


class DMMessageEditedEvent(BaseEvent):
    type: Literal["dm.message.edited"]
    workspace_id: str
    dm_id: str
    message_id: str
    content: str
    edited_at: str


class DMMessageDeletedEvent(BaseEvent):
    type: Literal["dm.message.deleted"]
    workspace_id: str
    dm_id: str
    message_id: str
    deleted_at: str


class WorkspaceMemberJoinedEvent(BaseEvent):
    type: Literal["workspace.member.joined"]
    workspace_id: str
    user_id: str
    joined_at: str


class WorkspaceMemberLeftEvent(BaseEvent):
    type: Literal["workspace.member.left"]
    workspace_id: str
    user_id: str


class ChannelCreatedEvent(BaseEvent):
    type: Literal["channel.created"]
    workspace_id: str
    channel_id: str
    channel_name: str


class ChannelDeletedEvent(BaseEvent):
    type: Literal["channel.deleted"]
    workspace_id: str
    channel_id: str

