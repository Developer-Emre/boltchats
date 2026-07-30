"""
All models for SparkQuark exported from one place
"""

from .conversation import (
    Assignment,
    Attachment,
    ConversationSource,
    ConversationStatus,
    Conversation,
    Customer,
    CustomerChannel,
    Draft,
    InternalNote,
    Label,
    Mention,
    Message,
    MessageFrom,
    MessageType,
)
from .identity import (
    Invitation,
    Member,
    MemberRole,
    Organization,
    PermissionEnum,
    RoleDocument,
    RoleEnum,
    Team,
)
from .integration import (
    ActionEnum,
    AuditLog,
    DomainEvent,
    EventType,
    Integration,
    IntegrationStatus,
    Notification,
    NotificationChannel,
    NotificationStatus,
    OAuthToken,
    ProviderEnum,
)

__all__ = [
    # Identity
    "Organization",
    "Member",
    "Team",
    "Invitation",
    "RoleDocument",
    "RoleEnum",
    "PermissionEnum",
    "MemberRole",
    # Conversation
    "Conversation",
    "Customer",
    "CustomerChannel",
    "Message",
    "Attachment",
    "InternalNote",
    "Mention",
    "Label",
    "Draft",
    "Assignment",
    "ConversationStatus",
    "ConversationSource",
    "MessageType",
    "MessageFrom",
    # Integration
    "Integration",
    "OAuthToken",
    "ProviderEnum",
    "IntegrationStatus",
    # Events & Audit
    "DomainEvent",
    "EventType",
    "AuditLog",
    "ActionEnum",
    # Notifications
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
]
