"""
Base Service Class

Common patterns for all services:
- Multi-tenancy enforcement
- Error handling
- Event publishing
- Logging
"""

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = structlog.get_logger()


class BaseService:
    """Base service with common patterns"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def log_action(
        self,
        action: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Log action for audit trail.
        
        Args:
            action: Action type (create, update, delete, etc.)
            resource_id: ID of affected resource
            resource_type: Type of resource
            details: Additional context
        """
        context = {
            "action": action,
            "resource_id": resource_id,
            "resource_type": resource_type,
        }
        if details:
            context.update(details)
        
        await logger.ainfo(action, **context)

    def check_organization_access(self, org_id: str, required_org_id: str) -> None:
        """Check that requested org matches authenticated org.
        
        Multi-tenancy enforcement: prevent data leakage.
        
        Args:
            org_id: Requested organization ID
            required_org_id: Authenticated organization ID
            
        Raises:
            PermissionError: If org_id doesn't match
        """
        if org_id != required_org_id:
            raise PermissionError(f"Access denied to organization {org_id}")

    def check_not_none(self, value: object, field_name: str) -> None:
        """Check that value is not None.
        
        Args:
            value: Value to check
            field_name: Field name for error message
            
        Raises:
            ValueError: If value is None
        """
        if value is None:
            raise ValueError(f"{field_name} is required")

    async def publish_event(
        self,
        event_type: str,
        organization_id: str,
        entity_id: str,
        entity_type: str,
        data: dict,
        actor_id: str | None = None,
    ) -> None:
        """Publish domain event (queued for async processing).
        
        Args:
            event_type: Event type (e.g., "conversation.created")
            organization_id: Organization context
            entity_id: ID of affected entity
            entity_type: Type of entity (conversation, message, etc.)
            data: Event payload
            actor_id: User who triggered event
        """
        from app.models.integration import DomainEvent
        from datetime import datetime, timezone
        
        event = DomainEvent(
            organization_id=organization_id,
            event_type=event_type,
            entity_id=entity_id,
            entity_type=entity_type,
            data=data,
            actor_id=actor_id,
            created_at=datetime.now(timezone.utc),
        )
        
        # Insert into events collection
        from app.repositories import DomainEventRepository
        repo = DomainEventRepository(self.db)
        event_id = await repo.create(event)
        
        # Queue for async processing (Redis)
        import json
        from app.core.redis import get_redis
        
        redis = get_redis()
        await redis.lpush(
            "sparkquark:event_queue",
            json.dumps({
                "event_id": event_id,
                "event_type": event_type,
                "organization_id": organization_id,
            })
        )
        
        await logger.ainfo("event_published", event_id=event_id, event_type=event_type)


class AppError(Exception):
    """Base application error"""

    def __init__(self, message: str, code: str = "ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found"""

    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} with ID {resource_id} not found"
        super().__init__(message, "NOT_FOUND", 404)


class ConflictError(AppError):
    """Resource already exists"""

    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)


class UnauthorizedError(AppError):
    """Authentication failed"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)


class ForbiddenError(AppError):
    """Authorization failed"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", 403)


class ValidationError(AppError):
    """Validation failed"""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class InvalidTokenError(UnauthorizedError):
    """Token is invalid or expired"""

    def __init__(self):
        super().__init__("Invalid or expired token")


class PermissionDeniedError(ForbiddenError):
    """User lacks required permission"""

    def __init__(self, permission: str):
        super().__init__(f"Permission denied: {permission}")
