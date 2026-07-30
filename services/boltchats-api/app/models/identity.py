"""
Identity Domain Models for SparkQuark

Organizations, Members, Teams, Roles, Permissions
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ─── ROLES ────────────────────────────────────────────────────────────

class RoleEnum(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class PermissionEnum(str, Enum):
    """All possible permissions in SparkQuark"""

    # Organization
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"

    # Members
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"
    MEMBER_DELETE = "member:delete"

    # Teams
    TEAM_READ = "team:read"
    TEAM_WRITE = "team:write"
    TEAM_DELETE = "team:delete"

    # Conversations
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_WRITE = "conversation:write"
    CONVERSATION_DELETE = "conversation:delete"

    # Messages
    MESSAGE_READ = "message:read"
    MESSAGE_WRITE = "message:write"
    MESSAGE_DELETE = "message:delete"

    # Internal Notes
    INTERNAL_NOTE_READ = "internal_note:read"
    INTERNAL_NOTE_WRITE = "internal_note:write"
    INTERNAL_NOTE_DELETE = "internal_note:delete"

    # Labels
    LABEL_READ = "label:read"
    LABEL_WRITE = "label:write"
    LABEL_DELETE = "label:delete"

    # Assignments
    ASSIGNMENT_READ = "assignment:read"
    ASSIGNMENT_WRITE = "assignment:write"
    ASSIGNMENT_DELETE = "assignment:delete"

    # Customers
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    CUSTOMER_DELETE = "customer:delete"

    # Integrations
    INTEGRATION_READ = "integration:read"
    INTEGRATION_WRITE = "integration:write"
    INTEGRATION_DELETE = "integration:delete"

    # Analytics
    ANALYTICS_READ = "analytics:read"

    # Audit Logs
    AUDIT_LOG_READ = "audit_log:read"


class RoleDocument(BaseModel):
    """Represents a role with permissions"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    name: str  # owner, admin, manager, agent, viewer
    permissions: list[PermissionEnum] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── ORGANIZATION ─────────────────────────────────────────────────────

class Organization(BaseModel):
    """Represents a SparkQuark organization (workspace equivalent)"""

    id: str | None = Field(default=None, alias="_id")
    name: str
    slug: str  # unique, URL-safe
    description: str = ""
    logo_url: str | None = None

    owner_id: str  # User who created the org
    members: list[str] = Field(default_factory=list)  # User IDs

    settings: dict = Field(default_factory=dict)
    # Example: { "message_retention_days": 90, "allow_external_sharing": True }

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ─── WORKSPACE ────────────────────────────────────────────────────────

class Workspace(BaseModel):
    """Workspace within organization (e.g., Support, Marketing, HR)"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    name: str
    description: str = ""
    
    # Workspace-specific settings
    settings: dict = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ─── MEMBER ───────────────────────────────────────────────────────────

class MemberStatus(str, Enum):
    """Member status in organization"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVITED = "invited"
    SUSPENDED = "suspended"


class Member(BaseModel):
    """Organization member"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    user_id: str  # Reference to User collection

    status: MemberStatus = MemberStatus.ACTIVE
    team_ids: list[str] = Field(default_factory=list)  # Team IDs

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ─── MEMBER ROLE ───────────────────────────────────────────────────────

class MemberRole(BaseModel):
    """Member's role assignment (separate for audit, expiry, delegation)"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    member_id: str
    role_id: str
    
    # Audit trail
    assigned_by: str  # Who assigned this role
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Future support: temporary roles, delegation
    expires_at: datetime | None = None
    delegated_to: str | None = None  # For delegation scenarios
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ─── TEAM ─────────────────────────────────────────────────────────────

class Team(BaseModel):
    """Support team or department within organization"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str
    name: str
    description: str = ""

    members: list[str] = Field(default_factory=list)  # Member IDs
    manager_ids: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ─── INVITATION ───────────────────────────────────────────────────────

class Invitation(BaseModel):
    """Email-based invitation to join organization"""

    id: str | None = Field(default=None, alias="_id")
    organization_id: str

    invited_email: str
    invited_by: str  # Member ID
    role: RoleEnum = RoleEnum.AGENT

    token: str  # Unique invitation token
    expires_at: datetime

    accepted: bool = False
    accepted_at: datetime | None = None
    accepted_by: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
