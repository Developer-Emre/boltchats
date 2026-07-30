"""
Integration & Events Models for SparkQuark

OAuth, Integrations, Domain Events, Audit Logs
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ─── INTEGRATION ──────────────────────────────────────────────────────

class ProviderEnum(str, Enum):
    """External providers"""

    META = "meta"  # Instagram, Facebook, WhatsApp
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"
    EMAIL = "email"
    LIVE_CHAT = "live_chat"


class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"


class Integration(BaseModel):
    """Connected external provider"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str

    provider: ProviderEnum
    name: str  # "Support Team Instagram", etc.
    
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    
    # OAuth
    oauth_token_id: str | None = None  # Reference to oauth_tokens collection
    webhook_url: str | None = None
    webhook_secret: str | None = None

    # Configuration
    settings: dict = Field(default_factory=dict)
    # Example for Meta: { "instagram_business_account_id": "123", "page_id": "456" }

    connected_by: str  # Member ID
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None

    error_message: str | None = None
    error_at: datetime | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── OAUTH TOKEN ───────────────────────────────────────────────────────

class OAuthToken(BaseModel):
    """Encrypted OAuth token for provider"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    integration_id: str

    provider: ProviderEnum
    
    # Tokens (encrypted in real scenario)
    access_token: str
    refresh_token: str | None = None
    
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    
    scope: str = ""  # Space-separated scopes
    
    raw_response: dict = Field(default_factory=dict)  # Store full OAuth response

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── DOMAIN EVENTS ────────────────────────────────────────────────────

class EventType(str, Enum):
    """Domain events"""

    # Conversation events
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_UPDATED = "conversation.updated"
    CONVERSATION_ASSIGNED = "conversation.assigned"
    CONVERSATION_STATUS_CHANGED = "conversation.status_changed"
    CONVERSATION_CLOSED = "conversation.closed"
    CONVERSATION_ARCHIVED = "conversation.archived"

    # Message events
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_EDITED = "message.edited"
    MESSAGE_DELETED = "message.deleted"

    # Internal note events
    INTERNAL_NOTE_CREATED = "internal_note.created"
    INTERNAL_NOTE_DELETED = "internal_note.deleted"

    # Mention events
    MENTION_CREATED = "mention.created"

    # Label events
    LABEL_CREATED = "label.created"
    LABEL_DELETED = "label.deleted"

    # Assignment events
    ASSIGNMENT_CREATED = "assignment.created"
    ASSIGNMENT_CHANGED = "assignment.changed"
    ASSIGNMENT_REMOVED = "assignment.removed"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"

    # Member events
    MEMBER_JOINED = "member.joined"
    MEMBER_LEFT = "member.left"

    # Organization events
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"


class DomainEvent(BaseModel):
    """Immutable domain event"""

    id: str | None = Field(default=None, alias="_id")
    event_type: EventType
    
    organization_id: str
    
    # Entity references
    entity_id: str  # ID of affected entity (conversation, message, etc.)
    entity_type: str  # Type of entity (conversation, message, etc.)
    
    # Event data
    data: dict = Field(default_factory=dict)  # Event-specific payload
    
    # Causality
    triggered_by: str | None = None  # Member ID or system
    caused_by: str | None = None  # Parent event ID if cascading
    
    # Metadata
    source: str = "api"  # api, webhook, automation, system
    ip_address: str | None = None
    user_agent: str | None = None
    
    # Ordering
    sequence: int = 0  # Event ordering within organization
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── AUDIT LOG ────────────────────────────────────────────────────────

class ActionEnum(str, Enum):
    """Audit log actions"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"


class AuditLog(BaseModel):
    """Immutable audit log entry"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    
    # Action
    action: ActionEnum
    resource_type: str  # conversation, message, member, etc.
    resource_id: str
    
    # Actor
    actor_id: str  # Member ID
    actor_email: str | None = None
    
    # Changes
    changes: dict = Field(default_factory=dict)
    # Example: { "status": { "from": "open", "to": "closed" } }
    
    # Context
    description: str = ""
    ip_address: str | None = None
    user_agent: str | None = None
    
    # Result
    success: bool = True
    error_message: str | None = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── NOTIFICATION ─────────────────────────────────────────────────────

class NotificationChannel(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    WEBSOCKET = "websocket"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class Notification(BaseModel):
    """Notification to be delivered"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    recipient_id: str  # Member ID
    
    # Content
    title: str
    body: str
    action_url: str | None = None
    
    # Delivery
    channel: NotificationChannel
    status: NotificationStatus = NotificationStatus.PENDING
    
    # References
    event_id: str | None = None  # Related DomainEvent
    entity_id: str | None = None  # Related entity (conversation, etc.)
    entity_type: str | None = None
    
    # Delivery attempts
    attempt_count: int = 0
    last_attempt_at: datetime | None = None
    last_error: str | None = None
    
    # Read status (for in-app)
    read: bool = False
    read_at: datetime | None = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = None
    delivered_at: datetime | None = None

    model_config = {"populate_by_name": True}
