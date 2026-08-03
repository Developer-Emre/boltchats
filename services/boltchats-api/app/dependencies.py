"""
Service dependency factories for FastAPI route handlers

These factories provide instances of service classes for dependency injection.
"""

from typing import AsyncGenerator
from fastapi import Depends

from app.core.database import get_database
from app.core.redis import get_redis


async def get_authentication_service() -> AsyncGenerator:
    """Get AuthenticationService instance"""
    from app.services.auth import AuthenticationService, TokenService
    from app.core.config import settings
    
    db = get_database()
    redis = get_redis()
    token_service = TokenService(redis, settings)
    service = AuthenticationService(db, redis, token_service)
    yield service


async def get_token_service() -> AsyncGenerator:
    """Get TokenService instance"""
    from app.services.auth import TokenService
    from app.core.config import settings
    
    redis = get_redis()
    service = TokenService(redis, settings)
    yield service


async def get_email_service() -> AsyncGenerator:
    """Get EmailService instance"""
    from app.services.email_service import EmailService
    from app.core.config import settings
    
    service = EmailService(
        api_key=settings.sendgrid_api_key,
        from_email=settings.email_from_address,
    )
    yield service


async def get_customer_service() -> AsyncGenerator:
    """Get CustomerService instance"""
    from app.services.conversation import CustomerService
    
    db = get_database()
    service = CustomerService(db)
    yield service


async def get_conversation_service() -> AsyncGenerator:
    """Get ConversationService instance"""
    from app.services.conversation import ConversationService
    
    db = get_database()
    service = ConversationService(db)
    yield service


async def get_message_service() -> AsyncGenerator:
    """Get MessageService instance"""
    from app.services.conversation import MessageService
    
    db = get_database()
    redis = get_redis()
    service = MessageService(db, redis)
    yield service


async def get_label_service() -> AsyncGenerator:
    """Get LabelService instance"""
    from app.services.conversation import LabelService
    
    db = get_database()
    service = LabelService(db)
    yield service


async def get_draft_service() -> AsyncGenerator:
    """Get DraftService instance"""
    from app.services.conversation import DraftService
    
    db = get_database()
    service = DraftService(db)
    yield service


async def get_integration_service() -> AsyncGenerator:
    """Get IntegrationService instance"""
    from app.services.integration import IntegrationService
    
    db = get_database()
    redis = get_redis()
    service = IntegrationService(db, redis)
    yield service


async def get_permission_service() -> AsyncGenerator:
    """Get PermissionService instance"""
    from app.services.security import PermissionService
    
    db = get_database()
    service = PermissionService(db)
    yield service


async def get_notification_service() -> AsyncGenerator:
    """Get NotificationService instance"""
    from app.services.notification import NotificationService
    
    db = get_database()
    redis = get_redis()
    service = NotificationService(db, redis)
    yield service


async def get_organization_service() -> AsyncGenerator:
    """Get OrganizationService instance"""
    from app.services.organization import OrganizationService
    
    db = get_database()
    service = OrganizationService(db)
    yield service


async def get_workspace_service() -> AsyncGenerator:
    """Get WorkspaceService instance"""
    from app.services.organization import WorkspaceService
    
    db = get_database()
    service = WorkspaceService(db)
    yield service


async def get_member_service() -> AsyncGenerator:
    """Get MemberService instance"""
    from app.services.organization import MemberService
    
    db = get_database()
    service = MemberService(db)
    yield service


async def get_team_service() -> AsyncGenerator:
    """Get TeamService instance"""
    from app.services.organization import TeamService
    
    db = get_database()
    service = TeamService(db)
    yield service


async def get_role_service() -> AsyncGenerator:
    """Get RoleService instance"""
    from app.services.organization import RoleService
    
    db = get_database()
    service = RoleService(db)
    yield service


async def get_invitation_service() -> AsyncGenerator:
    """Get InvitationService instance"""
    from app.services.organization import InvitationService
    
    db = get_database()
    service = InvitationService(db)
    yield service

