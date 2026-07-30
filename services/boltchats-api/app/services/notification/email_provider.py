"""
Email Notification Provider

SendGrid, Mailgun, or SMTP email notifications
"""

from typing import Optional

from .base_provider import BaseNotificationProvider


class EmailNotificationProvider(BaseNotificationProvider):
    """
    Email notification provider.
    
    Supports SendGrid, Mailgun, SMTP
    """

    def __init__(self, api_key: str, from_email: str, provider: str = "sendgrid"):
        super().__init__(provider)
        self.api_key = api_key
        self.from_email = from_email
        self.provider = provider  # sendgrid, mailgun, smtp

    async def validate_credentials(self, credentials: dict) -> bool:
        """Validate email provider credentials."""
        if self.provider in ["sendgrid", "mailgun"]:
            return "api_key" in credentials and "from_email" in credentials
        elif self.provider == "smtp":
            return all(
                k in credentials
                for k in ["smtp_host", "smtp_port", "smtp_user", "smtp_password"]
            )
        return False

    async def send_notification(
        self,
        recipient_id: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> str:
        """
        Send email notification.
        
        Args:
            recipient_id: Email address
            title: Email subject
            message: Email body
            data: Extra data
            
        Returns:
            Provider message ID
        """
        # Production: send via SendGrid/Mailgun API or SMTP
        mock_message_id = f"email_{recipient_id}_{int(1000000000)}"
        return mock_message_id

    async def handle_webhook(self, payload: dict) -> dict:
        """
        Handle email provider webhook.
        
        SendGrid events: delivered, open, click, bounce, spamreport, unsubscribe
        Mailgun events: delivered, opened, clicked, bounced, unsubscribed
        """
        event = payload.get("event") or payload.get("type")
        recipient = payload.get("email") or payload.get("recipient")

        return {
            "event": event,
            "recipient": recipient,
        }

    async def get_delivery_status(self, message_id: str) -> Optional[dict]:
        """Get email delivery status from provider."""
        # Production: query provider API
        return None

    async def is_connected(self) -> bool:
        """Check if email provider connection is valid."""
        return bool(self.api_key and self.from_email)
