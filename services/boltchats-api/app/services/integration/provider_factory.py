"""
Provider Factory

Factory pattern for creating provider instances
"""

from typing import Optional

from app.services.base import ValidationError

from .base_provider import BaseProvider
from .email_provider import EmailProvider
from .facebook_provider import FacebookProvider
from .instagram_provider import InstagramProvider
from .whatsapp_provider import WhatsAppProvider


class ProviderFactory:
    """Factory for creating provider adapters"""

    @staticmethod
    def create_provider(
        provider_name: str,
        credentials: dict,
    ) -> Optional[BaseProvider]:
        """
        Create provider instance based on name and credentials.
        
        Args:
            provider_name: Provider name (instagram, facebook, whatsapp, email)
            credentials: Provider-specific credentials
            
        Returns:
            Provider instance or None if unknown provider
            
        Raises:
            ValidationError: Missing required credentials
        """
        provider_name = provider_name.lower()

        if provider_name == "instagram":
            access_token = credentials.get("access_token")
            business_account_id = credentials.get("business_account_id")

            if not access_token or not business_account_id:
                raise ValidationError(
                    "Instagram requires: access_token, business_account_id"
                )

            return InstagramProvider(access_token, business_account_id)

        elif provider_name == "facebook":
            access_token = credentials.get("access_token")
            page_id = credentials.get("page_id")

            if not access_token or not page_id:
                raise ValidationError("Facebook requires: access_token, page_id")

            return FacebookProvider(access_token, page_id)

        elif provider_name == "whatsapp":
            access_token = credentials.get("access_token")
            phone_number_id = credentials.get("phone_number_id")

            if not access_token or not phone_number_id:
                raise ValidationError(
                    "WhatsApp requires: access_token, phone_number_id"
                )

            return WhatsAppProvider(access_token, phone_number_id)

        elif provider_name == "email":
            email = credentials.get("email")
            provider = credentials.get("provider", "smtp")

            if not email:
                raise ValidationError("Email requires: email")

            return EmailProvider(email, provider)

        else:
            raise ValidationError(f"Unknown provider: {provider_name}")

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported provider names."""
        return ["instagram", "facebook", "whatsapp", "email"]

    @staticmethod
    def get_required_credentials(provider_name: str) -> dict:
        """
        Get required credentials for provider.
        
        Returns:
            {field: description}
        """
        specs = {
            "instagram": {
                "access_token": "Meta Graph API access token",
                "business_account_id": "Instagram Business Account ID",
            },
            "facebook": {
                "access_token": "Meta Graph API access token",
                "page_id": "Facebook Page ID",
            },
            "whatsapp": {
                "access_token": "Meta Graph API access token",
                "phone_number_id": "WhatsApp Business Phone Number ID",
            },
            "email": {
                "email": "Email address",
                "provider": "Provider type (smtp, sendgrid, mailgun)",
                "smtp_host": "SMTP host (if smtp)",
                "smtp_port": "SMTP port (if smtp)",
                "smtp_user": "SMTP user (if smtp)",
                "smtp_password": "SMTP password (if smtp)",
                "api_key": "API key (if sendgrid or mailgun)",
            },
        }

        return specs.get(provider_name.lower(), {})
