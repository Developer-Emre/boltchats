"""
Conversation Domain Models for SparkQuark

Customers, Conversations, Messages, Labels, Assignments, Internal Notes, Mentions
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ─── ENUMS ────────────────────────────────────────────────────────────

class ConversationStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ConversationChannel(str, Enum):
    """Communication channel (provider)"""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    FACEBOOK_MESSENGER = "facebook_messenger"
    WHATSAPP = "whatsapp"
    LIVE_CHAT = "live_chat"
    EMAIL = "email"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LINK = "link"


class MessageFrom(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    INTERNAL = "internal"


# ─── CUSTOMER & CUSTOMER IDENTITY ─────────────────────────────────────

class CustomerIdentity(BaseModel):
    """Customer's identifier on a specific channel (separate collection)"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    customer_id: str

    channel: ConversationChannel
    external_id: str  # Platform-specific ID (Instagram ID, WhatsApp number, etc.)
    username: str | None = None  # Display username (e.g., @instagram_handle)
    
    # Channel-specific metadata
    metadata: dict = Field(default_factory=dict)  # avatar_url, phone, etc.

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class CustomerStats(BaseModel):
    """Embedded stats for Customer (denormalized for dashboard queries)"""

    conversation_count: int = 0
    open_conversation_count: int = 0
    closed_conversation_count: int = 0
    total_messages: int = 0
    last_contact_at: datetime | None = None


class Customer(BaseModel):
    """Unified customer profile across all channels"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str

    # Basic info
    name: str
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None

    # Embedded stats (denormalized for dashboard queries)
    stats: CustomerStats = Field(default_factory=CustomerStats)

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── CONVERSATION ─────────────────────────────────────────────────────

class Assignment(BaseModel):
    """Who is handling this conversation"""

    member_id: str
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_by: str  # Member ID who made assignment


class Conversation(BaseModel):
    """A conversation thread with a customer"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    customer_id: str

    # Channel and identity
    channel: ConversationChannel
    external_id: str  # Instagram DM ID, WhatsApp message ID, etc.
    external_url: str | None = None

    # Status
    status: ConversationStatus = ConversationStatus.OPEN
    status_changed_at: datetime | None = None
    status_changed_by: str | None = None

    # Assignment
    assigned_to: Assignment | None = None
    team_id: str | None = None

    # Metadata
    subject: str | None = None
    label_ids: list[str] = Field(default_factory=list)  # Label IDs (renamed from labels)
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    tags: list[str] = Field(default_factory=list)

    # Denormalized counts for dashboard queries
    message_count: int = 0
    last_message_id: str | None = None
    last_message_at: datetime | None = None
    participant_count: int = 0  # Number of team members involved

    # Internal collaboration
    mention_count: int = 0
    internal_note_count: int = 0

    # Metadata
    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    archived_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ─── CONVERSATION PARTICIPANT ─────────────────────────────────────────

class ConversationParticipant(BaseModel):
    """Team member participating in a conversation"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str
    member_id: str

    # Tracking
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_read_message_id: str | None = None
    last_read_at: datetime | None = None

    # Metadata
    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── MESSAGE ───────────────────────────────────────────────────────────

class Mention(BaseModel):
    """Embedded @mention in message or internal note"""

    member_id: str
    mentioned_by: str  # Member ID who created the mention
    mentioned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Attachment(BaseModel):
    """Embedded file attachment in a message"""

    url: str
    filename: str
    size: int  # bytes
    mime_type: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(BaseModel):
    """Message in a conversation"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str

    # Content
    content: str
    message_type: MessageType = MessageType.TEXT
    
    # Embedded attachments and mentions (MongoDB advantage)
    attachments: list[Attachment] = Field(default_factory=list)
    mentions: list[Mention] = Field(default_factory=list)

    # Who sent it
    from_type: MessageFrom  # customer or agent
    sender_id: str | None = None  # Agent Member ID if from_type=agent
    customer_id: str | None = None  # Customer ID if from_type=customer

    # External reference
    external_id: str | None = None  # Instagram message ID, etc.

    # Threading support
    reply_to_message_id: str | None = None  # For threaded conversations

    # Edit history
    edited_at: datetime | None = None
    edited_by: str | None = None

    # Soft delete
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: str | None = None

    # Metadata
    metadata: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── INTERNAL NOTE ─────────────────────────────────────────────────────

class InternalNote(BaseModel):
    """Team-only note (never visible to customer)"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str

    content: str
    author_id: str  # Member ID
    
    # Embedded mentions (same as Message)
    mentions: list[Mention] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── LABEL ────────────────────────────────────────────────────────────

class Label(BaseModel):
    """Category/tag for conversations"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str

    name: str
    color: str = "#3b82f6"  # Hex color
    icon: str | None = None
    description: str = ""

    conversation_count: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── DRAFT ────────────────────────────────────────────────────────────

class ConversationDraft(BaseModel):
    """Unsent message draft (simplified)"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str
    member_id: str

    content: str
    attachments: list[Attachment] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
