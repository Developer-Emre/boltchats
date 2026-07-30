"""
Instagram Provider

Instagram-specific adapter
"""

from .meta_provider import MetaProvider


class InstagramProvider(MetaProvider):
    """
    Instagram DM provider.
    
    Inherits from MetaProvider for Meta Graph API integration.
    """

    def __init__(self, access_token: str, business_account_id: str):
        super().__init__("instagram", access_token)
        self.business_account_id = business_account_id
        self.graph_api_url = f"https://graph.instagram.com/v18.0"

    async def get_user_profile(self, user_id: str):
        """Get Instagram user profile."""
        # Production: GET /user_id with fields=username,name,profile_pic_url
        return {
            "id": user_id,
            "username": f"instagram_user_{user_id}",
            "name": "Instagram User",
            "profile_pic_url": None,
            "verified": False,
        }
