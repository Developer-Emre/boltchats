"""
MongoDB Collections and Constants for SparkQuark
"""

from enum import Enum


class Collection(str, Enum):
    """MongoDB collection names"""

    # Identity Domain
    ORGANIZATIONS = "organizations"
    MEMBERS = "members"
    ROLES = "roles"
    TEAMS = "teams"
    INVITATIONS = "invitations"

    # Conversation Domain
    CUSTOMERS = "customers"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    INTERNAL_NOTES = "internal_notes"
    MENTIONS = "mentions"
    LABELS = "labels"
    DRAFTS = "drafts"

    # Integration Domain
    INTEGRATIONS = "integrations"
    OAUTH_TOKENS = "oauth_tokens"

    # Events & Audit
    EVENTS = "events"
    AUDIT_LOGS = "audit_logs"

    # Notifications
    NOTIFICATIONS = "notifications"
    NOTIFICATION_QUEUE = "notification_queue"


class ErrorMessage(str, Enum):
    """Standard error messages"""

    # Auth
    INVALID_CREDENTIALS = "Invalid email or password"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_INVALID = "Invalid token"
    UNAUTHORIZED = "Unauthorized"
    FORBIDDEN = "Forbidden"

    # Organization
    ORG_NOT_FOUND = "Organization not found"
    ORG_ALREADY_EXISTS = "Organization already exists"
    ORG_INVALID_SLUG = "Invalid organization slug"

    # Member
    MEMBER_NOT_FOUND = "Member not found"
    MEMBER_ALREADY_EXISTS = "Member already exists"
    MEMBER_NOT_ACTIVE = "Member is not active"

    # Team
    TEAM_NOT_FOUND = "Team not found"
    TEAM_ALREADY_EXISTS = "Team already exists"

    # Role
    ROLE_NOT_FOUND = "Role not found"
    ROLE_ALREADY_EXISTS = "Role already exists"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"

    # Conversation
    CONVERSATION_NOT_FOUND = "Conversation not found"
    CONVERSATION_ALREADY_EXISTS = "Conversation already exists"
    CONVERSATION_INVALID_STATUS = "Invalid conversation status"

    # Customer
    CUSTOMER_NOT_FOUND = "Customer not found"
    CUSTOMER_ALREADY_EXISTS = "Customer already exists"

    # Message
    MESSAGE_NOT_FOUND = "Message not found"
    MESSAGE_INVALID_TYPE = "Invalid message type"

    # Integration
    INTEGRATION_NOT_FOUND = "Integration not found"
    INTEGRATION_ALREADY_CONNECTED = "Integration already connected"
    INTEGRATION_CONNECTION_FAILED = "Failed to connect integration"
    PROVIDER_NOT_SUPPORTED = "Provider not supported"

    # Invitation
    INVITATION_NOT_FOUND = "Invitation not found"
    INVITATION_EXPIRED = "Invitation has expired"
    INVITATION_ALREADY_ACCEPTED = "Invitation already accepted"

    # Validation
    INVALID_EMAIL = "Invalid email address"
    INVALID_URL = "Invalid URL"
    INVALID_PARAMETER = "Invalid parameter"
    MISSING_REQUIRED_FIELD = "Missing required field"

    # Server
    INTERNAL_ERROR = "Internal server error"
    DATABASE_ERROR = "Database operation failed"
    EXTERNAL_API_ERROR = "External API error"


class IndexName(str, Enum):
    """MongoDB index names"""

    # Organizations
    ORG_SLUG_UNIQUE = "organizations_slug_unique"
    ORG_CREATED_AT = "organizations_created_at"

    # Members
    MEMBER_ORG_USER = "members_org_user_unique"
    MEMBER_ORG_ID = "members_organization_id"

    # Teams
    TEAM_ORG_ID = "teams_organization_id"

    # Conversations
    CONV_ORG_ID = "conversations_organization_id"
    CONV_CUSTOMER_ID = "conversations_customer_id"
    CONV_STATUS = "conversations_status"
    CONV_EXTERNAL_ID = "conversations_external_id_unique"
    CONV_UPDATED_AT = "conversations_updated_at"

    # Messages
    MSG_CONVERSATION_ID = "messages_conversation_id"
    MSG_EXTERNAL_ID = "messages_external_id_unique"
    MSG_CREATED_AT = "messages_created_at"

    # Customers
    CUSTOMER_ORG_ID = "customers_organization_id"
    CUSTOMER_EMAIL = "customers_email"

    # Events
    EVENT_ORG_ID = "events_organization_id"
    EVENT_TYPE = "events_event_type"
    EVENT_CREATED_AT = "events_created_at"

    # Audit Logs
    AUDIT_ORG_ID = "audit_logs_organization_id"
    AUDIT_ACTOR_ID = "audit_logs_actor_id"
    AUDIT_CREATED_AT = "audit_logs_created_at"

    # Integrations
    INTEGRATION_ORG_PROVIDER = "integrations_org_provider_unique"

    # Notifications
    NOTIF_RECIPIENT_ID = "notifications_recipient_id"
    NOTIF_STATUS = "notifications_status"
    NOTIF_CREATED_AT = "notifications_created_at"


class RedisKey(str, Enum):
    """Redis key patterns for SparkQuark"""

    # Rate limiting
    RATE_LIMIT_API = "rate_limit:api:{ip}"
    RATE_LIMIT_LOGIN = "rate_limit:login:{email}"

    # Session
    SESSION_TOKEN = "session:token:{token}"
    REFRESH_TOKEN = "refresh_token:{token}"

    # Presence
    PRESENCE_ORG = "presence:org:{org_id}"
    PRESENCE_MEMBER = "presence:member:{member_id}"

    # Typing indicators
    TYPING_CONVERSATION = "typing:conversation:{conversation_id}:{member_id}"

    # Real-time subscriptions
    SUBSCRIBE_ORG = "org:{org_id}"
    SUBSCRIBE_CONVERSATION = "conversation:{conversation_id}"
    SUBSCRIBE_CUSTOMER = "customer:{customer_id}"

    # Cache
    CACHE_MEMBER = "cache:member:{member_id}"
    CACHE_ORG = "cache:org:{org_id}"
    CACHE_CONVERSATION = "cache:conversation:{conversation_id}"

    # Message queue
    QUEUE_NOTIFICATIONS = "queue:notifications"
    QUEUE_EVENTS = "queue:events"
    QUEUE_INTEGRATIONS = "queue:integrations"
