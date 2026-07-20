from datetime import datetime

from pydantic import BaseModel, Field


class ChannelSettingsSchema(BaseModel):
    can_post: list[str] = Field(default_factory=lambda: ["member"])
    can_invite: list[str] = Field(default_factory=lambda: ["admin"])
    thread_replies_allowed: bool = True
    auto_join_new_members: bool = True
    posting_restrictions: str = "none"  # none, mods, owner


class CreateChannelRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=256)
    type: str = Field(default="public")  # public, private, shared_channel
    topic: str = Field(default="")
    purpose: str = Field(default="")


class UpdateChannelRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=256)
    topic: str | None = None
    purpose: str | None = None
    settings: ChannelSettingsSchema | None = None


class ChannelResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    display_name: str
    description: str
    type: str
    topic: str
    owner_id: str
    member_count: int
    message_count: int
    is_archived: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelDetailResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    display_name: str
    description: str
    type: str
    topic: str
    purpose: str
    owner_id: str
    members: list[str]
    settings: ChannelSettingsSchema
    member_count: int
    message_count: int
    is_archived: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelListResponse(BaseModel):
    items: list[ChannelResponse]
    next_cursor: str | None = None
