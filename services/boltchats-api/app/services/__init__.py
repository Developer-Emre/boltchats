"""
Services Layer - Business Logic

Service classes handle all business logic, validation, and orchestration.
They use repositories for data access and publish domain events.

Multi-tenant support is enforced at every service method.

Organized into domains:
- auth/ - User authentication (authentication, tokens, passwords)
- organization/ - Org structure (orgs, workspaces, members, teams, roles, invites)
- conversation/ - Customer communication (customers, conversations, messages, drafts, labels)
- security/ - Access control (permissions, RBAC)
- integration/ - Provider connections (Phase 5 ✅)
- notification/ - Multi-channel notifications (Phase 5 ✅)
- events/ - Event bus & workflow orchestration (Phase 6)
"""

from .auth import AuthenticationService, PasswordService, TokenService
from .base import (
    AppError,
    BaseService,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from .conversation import (
    ConversationService,
    CustomerService,
    DraftService,
    LabelService,
    MessageService,
)
from .integration import (
    IntegrationService,
    ProviderFactory,
)
from .notification import (
    NotificationProviderFactory,
    NotificationService,
)
from .organization import (
    InvitationService,
    MemberService,
    OrganizationService,
    RoleService,
    TeamService,
    WorkspaceService,
)
from .security import Permission, PermissionService

__all__ = [
    # Base
    "BaseService",
    "AppError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    # Auth Services
    "AuthenticationService",
    "TokenService",
    "PasswordService",
    # Organization Services
    "OrganizationService",
    "WorkspaceService",
    "MemberService",
    "TeamService",
    "RoleService",
    "InvitationService",
    # Conversation Services
    "CustomerService",
    "ConversationService",
    "MessageService",
    "DraftService",
    "LabelService",
    # Security Services
    "PermissionService",
    "Permission",
    # Integration Services
    "IntegrationService",
    "ProviderFactory",
    # Notification Services
    "NotificationService",
    "NotificationProviderFactory",
]
