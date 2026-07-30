"""
All models for SparkQuark exported from one place
"""

from .conversation import (
    Assignment,
    Attachment,
    Conversation,
    ConversationChannel,
    ConversationDraft,
    ConversationParticipant,
    ConversationStatus,
    Customer,
    CustomerIdentity,
    CustomerStats,
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
    MemberStatus,
    Organization,
    PermissionEnum,
    RoleDocument,
    RoleEnum,
    Team,
    User,
    Workspace,
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
    OAuthData,
    ProviderEnum,
)

__all__ = [
    # Identity
    "User",
    "Organization",
    "Workspace",
    "Member",
    "MemberStatus",
    "Team",
    "Invitation",
    "RoleDocument",
    "RoleEnum",
    "PermissionEnum",
    "MemberRole",
    # Conversation
    "Conversation",
    "ConversationParticipant",
    "Customer",
    "CustomerIdentity",
    "CustomerStats",
    "Message",
    "Attachment",
    "Mention",
    "InternalNote",
    "Label",
    "ConversationDraft",
    "Assignment",
    "ConversationStatus",
    "ConversationChannel",
    "MessageType",
    "MessageFrom",
    # Integration
    "Integration",
    "OAuthData",
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
