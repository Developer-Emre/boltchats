"""
Email Service

Send transactional emails (verification, reset, notifications)
"""

from typing import Optional

import structlog

logger = structlog.get_logger()


class EmailService:
    """Handle transactional emails"""

    def __init__(self, api_key: Optional[str] = None, from_email: str = "noreply@sparkquark.com"):
        """
        Initialize email service.
        
        Args:
            api_key: SendGrid/Mailgun API key (optional for dev/test)
            from_email: Sender email address
        """
        self.api_key = api_key
        self.from_email = from_email

    async def send_verification_email(
        self,
        to: str,
        name: str,
        token: str,
        frontend_url: str,
    ) -> None:
        """
        Send email verification link.
        
        Args:
            to: Recipient email
            name: User full name
            token: Email verification token
            frontend_url: Frontend base URL for verification link
        """
        verification_link = f"{frontend_url}/verify-email?token={token}"
        
        subject = "Verify your SparkQuark email"
        html_body = f"""
        <h2>Welcome to SparkQuark, {name}!</h2>
        <p>Please verify your email address to complete registration.</p>
        <p><a href="{verification_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
        <p>Or copy this link: <code>{verification_link}</code></p>
        <p>This link expires in 24 hours.</p>
        """
        
        await self._send(to, subject, html_body)
        await logger.ainfo("verification_email_sent", to=to)

    async def send_password_reset_email(
        self,
        to: str,
        name: str,
        token: str,
        frontend_url: str,
    ) -> None:
        """
        Send password reset link.
        
        Args:
            to: Recipient email
            name: User full name
            token: Password reset token
            frontend_url: Frontend base URL for reset link
        """
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        subject = "Reset your SparkQuark password"
        html_body = f"""
        <h2>Reset your password</h2>
        <p>Hi {name},</p>
        <p>We received a request to reset your password.</p>
        <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>Or copy this link: <code>{reset_link}</code></p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        
        await self._send(to, subject, html_body)
        await logger.ainfo("password_reset_email_sent", to=to)

    async def send_trial_expiring_email(
        self,
        to: str,
        name: str,
        org_name: str,
        days_left: int,
        upgrade_url: str,
    ) -> None:
        """
        Send trial expiration warning email.
        
        Args:
            to: Recipient email
            name: User full name
            org_name: Organization name
            days_left: Days remaining in trial
            upgrade_url: URL to upgrade page
        """
        subject = f"Your {org_name} trial ends in {days_left} days"
        html_body = f"""
        <h2>Your trial is expiring soon</h2>
        <p>Hi {name},</p>
        <p>Your <strong>{org_name}</strong> trial ends in <strong>{days_left} days</strong>.</p>
        <p>Upgrade now to keep using all features:</p>
        <p><a href="{upgrade_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Upgrade Now</a></p>
        <p>Choose from our plans: Basic ($29/mo), Pro ($99/mo), or Enterprise (custom).</p>
        """
        
        await self._send(to, subject, html_body)
        await logger.ainfo("trial_expiring_email_sent", to=to, days_left=days_left)

    async def send_trial_expired_email(
        self,
        to: str,
        name: str,
        org_name: str,
        upgrade_url: str,
    ) -> None:
        """
        Send trial expired notification email.
        
        Args:
            to: Recipient email
            name: User full name
            org_name: Organization name
            upgrade_url: URL to upgrade page
        """
        subject = f"Your {org_name} trial has expired"
        html_body = f"""
        <h2>Your trial has expired</h2>
        <p>Hi {name},</p>
        <p>Your <strong>{org_name}</strong> trial has ended.</p>
        <p>Upgrade now to continue using SparkQuark:</p>
        <p><a href="{upgrade_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Upgrade Now</a></p>
        """
        
        await self._send(to, subject, html_body)
        await logger.ainfo("trial_expired_email_sent", to=to)

    async def _send(self, to: str, subject: str, html_body: str) -> None:
        """
        Internal method to send email.
        
        In production, integrate with SendGrid/Mailgun.
        For now, logs the email (dev/test mode).
        
        Args:
            to: Recipient email
            subject: Email subject
            html_body: Email body (HTML)
        """
        if not self.api_key:
            # Development mode: just log
            await logger.ainfo("email_sent_dev", to=to, subject=subject)
            return
        
        # TODO: Integrate with SendGrid
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        # 
        # message = Mail(
        #     from_email=self.from_email,
        #     to_emails=to,
        #     subject=subject,
        #     html_content=html_body,
        # )
        # sg = SendGridAPIClient(self.api_key)
        # await sg.send(message)
        
        await logger.ainfo("email_sent", to=to, subject=subject)
