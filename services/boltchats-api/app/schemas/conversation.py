"""
Request/Response schemas for Conversation domain
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.conversation import (
    ConversationStatus,
    MessageType,
)


class CustomerCreateRequest(BaseModel):
    """Create customer request"""
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(BaseModel):
    """Customer response"""
    id: str
    organization_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    conversation_count: int
    message_count: int
    last_contact_at: Optional[datetime]
    created_at: datetime


class CustomerIdentityResponse(BaseModel):
    """Customer channel identity"""
    id: str
    customer_id: str
    provider: str  # instagram, facebook, whatsapp, email, etc
    external_id: str  # Provider's user ID
    username: Optional[str]
    metadata: dict


class ConversationCreateRequest(BaseModel):
    """Create conversation request"""
    customer_id: str
    channel: str  # instagram, facebook, whatsapp, email
    subject: Optional[str] = None


class ConversationUpdateRequest(BaseModel):
    """Update conversation request"""
    status: Optional[ConversationStatus] = None
    assigned_to: Optional[str] = None  # Member ID
    labels: Optional[list[str]] = None


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    organization_id: str
    customer_id: str
    channel: str
    subject: Optional[str]
    status: ConversationStatus
    assigned_to: Optional[str]
    last_message_id: Optional[str]
    last_message_at: Optional[datetime]
    message_count: int
    participant_count: int
    labels: list[str]
    created_at: datetime
    updated_at: datetime


class MessageCreateRequest(BaseModel):
    """Send message request"""
    conversation_id: str
    text: str = Field(..., min_length=1)
    message_type: Optional[MessageType] = MessageType.TEXT
    reply_to_message_id: Optional[str] = None
    metadata: Optional[dict] = None


class MessageUpdateRequest(BaseModel):
    """Edit message request"""
    text: str = Field(..., min_length=1)


class MessageDeleteRequest(BaseModel):
    """Delete message request (soft delete)"""
    reason: Optional[str] = None


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    conversation_id: str
    sender_id: str
    text: str
    message_type: MessageType
    reply_to_message_id: Optional[str]
    edited_at: Optional[datetime]
    edited_by: Optional[str]
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]
    metadata: dict
    created_at: datetime


class LabelCreateRequest(BaseModel):
    """Create label request"""
    name: str = Field(..., min_length=1)
    color: Optional[str] = None


class LabelUpdateRequest(BaseModel):
    """Update label request"""
    name: Optional[str] = None
    color: Optional[str] = None


class LabelResponse(BaseModel):
    """Label response"""
    id: str
    organization_id: str
    name: str
    color: Optional[str]
    conversation_count: int
    created_at: datetime


class DraftResponse(BaseModel):
    """Draft response"""
    id: str
    conversation_id: str
    member_id: str
    content: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Paginated conversation list"""
    items: list[ConversationResponse]
    total: int
    limit: int
    offset: int


class MessageListResponse(BaseModel):
    """Paginated message list"""
    items: list[MessageResponse]
    total: int
    limit: int
    offset: int
