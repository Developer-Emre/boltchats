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


class ConversationSource(str, Enum):
    """Communication channel source"""

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


# ─── CUSTOMER ─────────────────────────────────────────────────────────

class CustomerChannel(BaseModel):
    """Customer's identifier on a specific channel"""

    source: ConversationSource
    identifier: str  # phone, email, username, ID, etc.
    display_name: str | None = None


class Customer(BaseModel):
    """Unified customer profile across all channels"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str

    # Basic info
    name: str
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None

    # Channel identifiers (Instagram handle, WhatsApp number, etc.)
    channels: list[CustomerChannel] = Field(default_factory=list)

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    # Conversation stats
    total_conversations: int = 0
    open_conversations: int = 0
    closed_conversations: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime | None = None

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

    # Source and identity
    source: ConversationSource
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
    labels: list[str] = Field(default_factory=list)  # Label IDs
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    tags: list[str] = Field(default_factory=list)

    # Messages
    message_count: int = 0
    last_message_id: str | None = None
    last_message_at: datetime | None = None

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


# ─── MESSAGE ───────────────────────────────────────────────────────────

class Attachment(BaseModel):
    """File attachment in a message"""

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
    attachments: list[Attachment] = Field(default_factory=list)

    # Who sent it
    from_type: MessageFrom  # customer or agent
    sender_id: str | None = None  # Agent Member ID if from_type=agent
    customer_id: str | None = None  # Customer ID if from_type=customer

    # External reference
    external_id: str | None = None  # Instagram message ID, etc.

    # Metadata
    metadata: dict = Field(default_factory=dict)

    # Status
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: str | None = None

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
    mentioned_members: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── MENTION ───────────────────────────────────────────────────────────

class Mention(BaseModel):
    """@mention of a team member"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str
    message_id: str | None = None  # If in message
    internal_note_id: str | None = None  # If in internal note

    mentioned_member_id: str
    mentioned_by: str  # Member ID
    context: str = ""  # Why they were mentioned

    read: bool = False
    read_at: datetime | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class Draft(BaseModel):
    """Unsent message draft"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    conversation_id: str

    content: str
    author_id: str  # Member ID
    attachments: list[Attachment] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
