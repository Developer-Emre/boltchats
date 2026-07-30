"""
WhatsApp Provider

WhatsApp Cloud API provider
"""

from .meta_provider import MetaProvider


class WhatsAppProvider(MetaProvider):
    """
    WhatsApp Cloud API provider.
    
    Uses Meta's WhatsApp Business API.
    Inherits from MetaProvider for Meta Graph API integration.
    """

    def __init__(self, access_token: str, phone_number_id: str):
        super().__init__("whatsapp", access_token)
        self.phone_number_id = phone_number_id
        self.graph_api_url = f"https://graph.instagram.com/v18.0"

    async def get_user_profile(self, user_id: str):
        """Get WhatsApp user profile."""
        # Production: GET user info from WhatsApp API
        return {
            "id": user_id,
            "phone": user_id,  # WhatsApp uses phone as ID
            "name": "WhatsApp User",
            "profile_pic_url": None,
        }
