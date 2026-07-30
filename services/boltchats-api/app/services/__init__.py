"""
Services Layer - Business Logic

Service classes handle all business logic, validation, and orchestration.
They use repositories for data access and publish domain events.

Multi-tenant support is enforced at every service method.
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
from .organization import (
    InvitationService,
    MemberService,
    OrganizationService,
    RoleService,
    TeamService,
    WorkspaceService,
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
]
