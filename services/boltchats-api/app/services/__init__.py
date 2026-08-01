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
- events/ - Event bus & workflow orchestration (Phase 6 ✅)
"""

# Re-export exceptions from base (break circular import cycle)
from .base import (
    AppError,
    BaseService,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    # Base
    "BaseService",
    "AppError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
]


# Lazy-load heavy service modules to break circular imports
def __getattr__(name: str):
    """Lazy load services on demand to break circular import cycles"""
    
    if name == "AuthenticationService":
        from .auth import AuthenticationService
        return AuthenticationService
    elif name == "TokenService":
        from .auth import TokenService
        return TokenService
    elif name == "PasswordService":
        from .auth import PasswordService
        return PasswordService
    elif name == "OrganizationService":
        from .organization import OrganizationService
        return OrganizationService
    elif name == "WorkspaceService":
        from .organization import WorkspaceService
        return WorkspaceService
    elif name == "MemberService":
        from .organization import MemberService
        return MemberService
    elif name == "TeamService":
        from .organization import TeamService
        return TeamService
    elif name == "RoleService":
        from .organization import RoleService
        return RoleService
    elif name == "InvitationService":
        from .organization import InvitationService
        return InvitationService
    elif name == "CustomerService":
        from .conversation import CustomerService
        return CustomerService
    elif name == "ConversationService":
        from .conversation import ConversationService
        return ConversationService
    elif name == "MessageService":
        from .conversation import MessageService
        return MessageService
    elif name == "DraftService":
        from .conversation import DraftService
        return DraftService
    elif name == "LabelService":
        from .conversation import LabelService
        return LabelService
    elif name == "PermissionService":
        from .security import PermissionService
        return PermissionService
    elif name == "Permission":
        from .security import Permission
        return Permission
    elif name == "IntegrationService":
        from .integration import IntegrationService
        return IntegrationService
    elif name == "ProviderFactory":
        from .integration import ProviderFactory
        return ProviderFactory
    elif name == "NotificationService":
        from .notification import NotificationService
        return NotificationService
    elif name == "NotificationProviderFactory":
        from .notification import NotificationProviderFactory
        return NotificationProviderFactory
    elif name == "EventBus":
        from .events import EventBus
        return EventBus
    elif name == "EventConsumer":
        from .events import EventConsumer
        return EventConsumer
    elif name == "WorkflowService":
        from .events import WorkflowService
        return WorkflowService
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
