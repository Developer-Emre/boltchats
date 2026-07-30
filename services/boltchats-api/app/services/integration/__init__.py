"""
Integration Services

Provider adapters (Instagram, Facebook, WhatsApp, Email)
using Strategy/Adapter pattern
"""

from .base_provider import BaseProvider
from .email_provider import EmailProvider
from .facebook_provider import FacebookProvider
from .instagram_provider import InstagramProvider
from .integration_service import IntegrationService
from .meta_provider import MetaProvider
from .provider_factory import ProviderFactory
from .whatsapp_provider import WhatsAppProvider

__all__ = [
    # Providers
    "BaseProvider",
    "MetaProvider",
    "InstagramProvider",
    "FacebookProvider",
    "WhatsAppProvider",
    "EmailProvider",
    "ProviderFactory",
    # Service
    "IntegrationService",
]
