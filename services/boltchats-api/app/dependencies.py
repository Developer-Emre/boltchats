"""
Service dependency factories for FastAPI route handlers

These factories provide instances of service classes for dependency injection.
"""

from typing import AsyncGenerator
from fastapi import Depends

from app.core.database import get_database
from app.core.redis import get_redis
from app.services import (
    AuthenticationService,
    TokenService,
    CustomerService,
    ConversationService,
    MessageService,
    LabelService,
    DraftService,
    IntegrationService,
    PermissionService,
)


async def get_authentication_service() -> AsyncGenerator[AuthenticationService, None]:
    """Get AuthenticationService instance"""
    db = get_database()
    service = AuthenticationService(db)
    yield service


async def get_token_service() -> AsyncGenerator[TokenService, None]:
    """Get TokenService instance"""
    redis = get_redis()
    from app.core.config import settings
    service = TokenService(redis, settings)
    yield service


async def get_customer_service() -> AsyncGenerator[CustomerService, None]:
    """Get CustomerService instance"""
    db = get_database()
    service = CustomerService(db)
    yield service


async def get_conversation_service() -> AsyncGenerator[ConversationService, None]:
    """Get ConversationService instance"""
    db = get_database()
    service = ConversationService(db)
    yield service


async def get_message_service() -> AsyncGenerator[MessageService, None]:
    """Get MessageService instance"""
    db = get_database()
    redis = get_redis()
    service = MessageService(db, redis)
    yield service


async def get_label_service() -> AsyncGenerator[LabelService, None]:
    """Get LabelService instance"""
    db = get_database()
    service = LabelService(db)
    yield service


async def get_draft_service() -> AsyncGenerator[DraftService, None]:
    """Get DraftService instance"""
    db = get_database()
    service = DraftService(db)
    yield service


async def get_integration_service() -> AsyncGenerator[IntegrationService, None]:
    """Get IntegrationService instance"""
    db = get_database()
    redis = get_redis()
    service = IntegrationService(db, redis)
    yield service


async def get_permission_service() -> AsyncGenerator[PermissionService, None]:
    """Get PermissionService instance"""
    db = get_database()
    service = PermissionService(db)
    yield service
