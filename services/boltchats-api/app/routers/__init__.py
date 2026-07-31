"""API routers for all domains"""

from .auth import router as auth_router
from .conversations import router as conversations_router
from .integrations import router as integrations_router
from .organizations import router as organizations_router

__all__ = [
    "auth_router",
    "conversations_router",
    "organizations_router",
    "integrations_router",
]
