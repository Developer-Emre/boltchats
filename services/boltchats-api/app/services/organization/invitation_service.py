"""
Invitation Service

Organization invitation management
"""

import secrets
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import Invitation
from app.repositories import InvitationRepository, OrganizationRepository
from app.services.base import BaseService, ConflictError, NotFoundError, ValidationError


class InvitationService(BaseService):
    """Manage organization invitations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.invitations = InvitationRepository(db)
        self.organizations = OrganizationRepository(db)

    async def invite_member(
        self,
        org_id: str,
        email: str,
        role_id: str,
        invited_by: str,
    ) -> Invitation:
        """
        Send invitation to join organization.
        
        Args:
            org_id: Organization ID
            email: Invitee email
            role_id: Role to assign after acceptance
            invited_by: Member ID who sent invitation
            
        Returns:
            Invitation
        """
        # Check org exists
        org = await self.organizations.get_active(org_id)
        if not org:
            raise NotFoundError("Organization", org_id)

        # Check no pending invitation
        existing = await self.invitations.find_by_email(org_id, email)
        if existing and not existing.accepted_at:
            raise ConflictError(f"Pending invitation already sent to {email}")

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Create invitation (expires in 7 days)
        invitation = Invitation(
            organization_id=org_id,
            email=email,
            role_id=role_id,
            token=token,
            invited_by=invited_by,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        inv_id = await self.invitations.create(invitation)

        await self.log_action(
            "invitation_sent",
            resource_id=inv_id,
            resource_type="invitation",
            details={"email": email},
        )

        return await self.invitations.read(inv_id)

    async def get_invitation(self, token: str) -> Invitation:
        """Get invitation by token."""
        invitation = await self.invitations.find_by_token(token)
        if not invitation:
            raise NotFoundError("Invitation", token)
        return invitation

    async def accept_invitation(
        self,
        token: str,
    ) -> tuple[str, str]:
        """
        Accept invitation to join organization.
        
        Args:
            token: Invitation token
            
        Returns:
            (organization_id, role_id)
        """
        # Find invitation
        invitation = await self.get_invitation(token)

        # Check not expired
        if invitation.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Invitation has expired")

        # Check not already accepted
        if invitation.accepted_at:
            raise ValidationError("Invitation already accepted")

        # Accept invitation
        await self.invitations.update(invitation.id, {
            "accepted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "invitation_accepted",
            resource_id=invitation.id,
            resource_type="invitation",
        )

        return invitation.organization_id, invitation.role_id

    async def revoke_invitation(self, org_id: str, invitation_id: str) -> None:
        """Revoke pending invitation."""
        invitation = await self.invitations.read(invitation_id)
        if not invitation or invitation.organization_id != org_id:
            raise NotFoundError("Invitation", invitation_id)

        if invitation.accepted_at:
            raise ValidationError("Cannot revoke accepted invitation")

        await self.invitations.delete(invitation_id)

        await self.log_action(
            "invitation_revoked",
            resource_id=invitation_id,
            resource_type="invitation",
        )

    async def get_pending_invitations(
        self,
        org_id: str,
    ) -> list[Invitation]:
        """Get all pending invitations for organization."""
        invitations = await self.invitations.find({
            "organization_id": org_id,
            "accepted_at": None,
            "expires_at": {"$gt": datetime.now(timezone.utc)},
        })
        return invitations

    async def cleanup_expired_invitations(self, org_id: str) -> int:
        """Delete expired invitations."""
        expired = await self.invitations.find({
            "organization_id": org_id,
            "accepted_at": None,
            "expires_at": {"$lt": datetime.now(timezone.utc)},
        })

        count = 0
        for inv in expired:
            await self.invitations.delete(inv.id)
            count += 1

        self.logger.info(
            "expired_invitations_cleaned",
            org_id=org_id,
            count=count,
        )

        return count
