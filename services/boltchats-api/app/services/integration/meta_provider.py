"""
Meta Provider

Parent class for Meta (Facebook, Instagram, WhatsApp) providers
"""

from typing import Optional

from .base_provider import BaseProvider


class MetaProvider(BaseProvider):
    """
    Base provider for Meta platforms (Facebook, Instagram, WhatsApp).
    
    All Meta APIs share similar structure:
    - OAuth 2.0 with access tokens
    - Webhook for incoming messages
    - Graph API for sending
    """

    def __init__(self, provider_name: str, access_token: str):
        super().__init__(provider_name)
        self.access_token = access_token
        self.api_version = "v18.0"
        self.graph_api_url = f"https://graph.instagram.com/{self.api_version}"

    async def validate_credentials(self, credentials: dict) -> bool:
        """
        Validate Meta access token.
        
        Args:
            credentials: {access_token: str}
            
        Returns:
            True if valid
        """
        # In production: call Meta's debug token endpoint
        # For now: check token format
        token = credentials.get("access_token", "")
        return len(token) > 20

    async def handle_webhook(self, payload: dict) -> dict:
        """
        Handle Meta webhook.
        
        Meta sends:
        {
            "object": "instagram" or "page",
            "entry": [
                {
                    "id": "...",
                    "messaging": [{
                        "sender": {"id": "..."},
                        "recipient": {"id": "..."},
                        "message": {"text": "..."},
                        "timestamp": ...
                    }]
                }
            ]
        }
        """
        # Validate webhook (production: verify signature)
        entries = payload.get("entry", [])

        responses = []
        for entry in entries:
            messages = entry.get("messaging", [])
            for message in messages:
                response = await self._process_message(message)
                if response:
                    responses.append(response)

        return {"status": "ok", "processed": len(responses)}

    async def _process_message(self, message: dict) -> Optional[dict]:
        """Process individual message from Meta webhook."""
        sender_id = message.get("sender", {}).get("id")
        recipient_id = message.get("recipient", {}).get("id")
        text = message.get("message", {}).get("text")
        timestamp = message.get("timestamp")

        return {
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "text": text,
            "timestamp": timestamp,
        }

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        attachments: Optional[list] = None,
    ) -> str:
        """
        Send message via Meta API.
        
        In production: call Graph API
        For now: return mock ID
        """
        # Production: POST to {graph_url}/{page_id}/messages
        # with {recipient_id, message: {text}}
        
        mock_message_id = f"meta_{recipient_id}_{int(1000000000)}"
        return mock_message_id

    async def get_message(self, message_id: str) -> Optional[dict]:
        """Get message details from Meta."""
        # Production: GET from Graph API
        return None

    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """
        Get user profile from Meta.
        
        Returns fields like name, profile picture, etc.
        """
        # Production: GET /{user_id} from Graph API
        return {
            "id": user_id,
            "name": "User",
            "profile_pic_url": None,
        }

    async def disconnect(self) -> None:
        """Disconnect from Meta (revoke access)."""
        # Production: POST to /{page_id}/subscribed_apps with unsubscribe
        pass

    async def is_connected(self) -> bool:
        """Check if Meta connection is still valid."""
        # Production: call debug token endpoint
        return bool(self.access_token)

    async def refresh_credentials(self) -> dict:
        """Refresh Meta token (if using refresh token)."""
        # Production: call OAuth refresh endpoint
        return {"access_token": self.access_token}
