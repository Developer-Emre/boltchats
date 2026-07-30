"""
Services Layer - Business Logic

Service classes handle all business logic, validation, and orchestration.
They use repositories for data access and publish domain events.

Multi-tenant support is enforced at every service method.
"""

from .auth_service import AuthService
from .base import (
    AppError,
    BaseService,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from .conversation_service import ConversationService, CustomerService
from .event_publisher import EventPublisher, EventSubscriber
from .integration_service import IntegrationService
from .notification_service import NotificationService
from .organization_service import OrganizationService

__all__ = [
    # Base
    "BaseService",
    "AppError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    # Services
    "AuthService",
    "OrganizationService",
    "CustomerService",
    "ConversationService",
    "NotificationService",
    "EventPublisher",
    "EventSubscriber",
    "IntegrationService",
]
