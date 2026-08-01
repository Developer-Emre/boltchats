"""
Message schemas for validation and serialization

Ensures messages conform to required format:
- Content validation (not empty, max length)
- Metadata validation
- Required fields present
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageChannel(str, Enum):
    """Supported message channels"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    SLACK = "slack"
    SMS = "sms"
    API = "api"


class MessageStatus(str, Enum):
    """Message processing status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class MessageBase(BaseModel):
    """Base message schema"""
    content: str = Field(..., min_length=1, max_length=10000)
    channel: MessageChannel = Field(default=MessageChannel.WEBSOCKET)
    metadata: Optional[dict] = Field(default_factory=dict)

    @validator("content")
    def content_not_empty(cls, v):
        """Content must not be empty or whitespace-only"""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()

    @validator("metadata", pre=True, always=True)
    def validate_metadata(cls, v):
        """Metadata must be a dict"""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v


class MessageCreate(MessageBase):
    """Schema for creating a message (from WebSocket/API)"""
    conversation_id: str = Field(..., min_length=1)

    class Config:
        use_enum_values = True


class MessageInDB(MessageBase):
    """Schema for message in database"""
    id: str = Field(...)
    conversation_id: str = Field(...)
    sender_id: str = Field(...)
    status: MessageStatus = Field(default=MessageStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)

    class Config:
        use_enum_values = True


class MessageResponse(MessageInDB):
    """Schema for API response"""
    
    class Config:
        use_enum_values = True


class MessageEdit(BaseModel):
    """Schema for message edit"""
    content: str = Field(..., min_length=1, max_length=10000)

    @validator("content")
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class MessageDelete(BaseModel):
    """Schema for message deletion (soft delete)"""
    hard_delete: bool = Field(default=False)


class ReactionBase(BaseModel):
    """Base reaction schema"""
    emoji: str = Field(..., min_length=1, max_length=10)
    
    @validator("emoji")
    def emoji_valid(cls, v):
        """Validate emoji format"""
        import re
        # Simple check for emoji pattern
        if not re.match(r'[\U0001F300-\U0001F9FF]|[\u2600-\u27BF]|[\u2300-\u23FF]', v):
            # Allow simple text emoji names like :heart:
            if not re.match(r'^:[a-z_]+:$', v):
                raise ValueError("Invalid emoji format")
        return v


class ReactionCreate(ReactionBase):
    """Schema for adding reaction"""
    message_id: str = Field(...)


class ReactionInDB(ReactionCreate):
    """Reaction in database"""
    id: str = Field(...)
    user_id: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReactionResponse(ReactionInDB):
    """Reaction API response"""
    pass


class MessageWithReactions(MessageResponse):
    """Message with reactions"""
    reactions: list[ReactionResponse] = Field(default_factory=list)
    reaction_count: int = Field(default=0)


class MessageBatch(BaseModel):
    """Batch of messages for bulk operations"""
    messages: list[MessageInDB]
    count: int = Field(ge=0)
    cursor: Optional[str] = Field(default=None)  # For pagination


class MessageConfirmation(BaseModel):
    """Message confirmation from WebSocket"""
    message_id: str = Field(...)
    status: MessageStatus = Field(default=MessageStatus.SENT)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = Field(default=None)


class QueueMessage(BaseModel):
    """Format for messages in Redis queue"""
    id: str = Field(...)
    conversation_id: str = Field(...)
    sender_id: str = Field(...)
    content: str = Field(...)
    channel: MessageChannel = Field(default=MessageChannel.WEBSOCKET)
    created_at: str = Field(...)  # ISO format
    metadata: dict = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0)

    class Config:
        use_enum_values = True
