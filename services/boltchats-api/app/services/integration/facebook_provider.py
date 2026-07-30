"""
Facebook Provider

Facebook Messenger provider
"""

from .meta_provider import MetaProvider


class FacebookProvider(MetaProvider):
    """
    Facebook Messenger provider.
    
    Inherits from MetaProvider for Meta Graph API integration.
    """

    def __init__(self, access_token: str, page_id: str):
        super().__init__("facebook", access_token)
        self.page_id = page_id
        self.graph_api_url = f"https://graph.facebook.com/v18.0"

    async def get_user_profile(self, user_id: str):
        """Get Facebook user profile."""
        # Production: GET /user_id with fields=name,profile_pic
        return {
            "id": user_id,
            "name": "Facebook User",
            "profile_pic_url": None,
        }
