"""
Conversation Service

Conversation management, inbox, assignment
"""

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import (
    Conversation,
    ConversationChannel,
    ConversationParticipant,
    ConversationStatus,
)
from app.repositories import (
    ConversationParticipantRepository,
    ConversationRepository,
    CustomerRepository,
)
from app.services.base import BaseService, NotFoundError, ValidationError


class ConversationService(BaseService):
    """Manage conversations with customers"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.conversations = ConversationRepository(db)
        self.participants = ConversationParticipantRepository(db)
        self.customers = CustomerRepository(db)

    async def create_conversation(
        self,
        org_id: str,
        customer_id: str,
        channel: ConversationChannel,
        assigned_to: Optional[str] = None,
    ) -> Conversation:
        """
        Create new conversation with customer.
        
        Args:
            org_id: Organization ID
            customer_id: Customer ID
            channel: Channel (instagram, whatsapp, email, facebook)
            assigned_to: Member ID to assign to (optional)
            
        Returns:
            Conversation
        """
        # Check customer exists
        customer = await self.customers.read(customer_id)
        if not customer or customer.organization_id != org_id:
            raise NotFoundError("Customer", customer_id)

        # Create conversation
        conv = Conversation(
            organization_id=org_id,
            customer_id=customer_id,
            channel=channel,
            status=ConversationStatus.OPEN,
            assigned_to=assigned_to,
        )
        conv_id = await self.conversations.create(conv)

        # Add initial participant if assigned
        if assigned_to:
            participant = ConversationParticipant(
                conversation_id=conv_id,
                member_id=assigned_to,
                joined_at=datetime.now(timezone.utc),
            )
            await self.participants.create(participant)

        await self.log_action(
            "conversation_created",
            resource_id=conv_id,
            resource_type="conversation",
            details={"channel": channel},
        )

        return await self.conversations.read(conv_id)

    async def get_conversation(
        self,
        org_id: str,
        conv_id: str,
    ) -> Conversation:
        """Get conversation details."""
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)
        return conv

    async def get_inbox(
        self,
        org_id: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """
        Get conversations in inbox (open or unresolved).
        
        Args:
            org_id: Organization ID
            status: Filter by status (optional)
            limit: Max results
            offset: Pagination offset
            
        Returns:
            List of conversations
        """
        return await self.conversations.find_inbox(
            org_id, status, limit, offset
        )

    async def update_conversation_status(
        self,
        org_id: str,
        conv_id: str,
        status: ConversationStatus,
    ) -> Conversation:
        """
        Update conversation status.
        
        Valid transitions:
        - OPEN → ASSIGNED or CLOSED
        - ASSIGNED → CLOSED
        - CLOSED → OPEN (reopen)
        """
        conv = await self.get_conversation(org_id, conv_id)

        # Validate transition
        valid_transitions = {
            ConversationStatus.OPEN: [
                ConversationStatus.ASSIGNED,
                ConversationStatus.CLOSED,
            ],
            ConversationStatus.ASSIGNED: [ConversationStatus.CLOSED],
            ConversationStatus.CLOSED: [ConversationStatus.OPEN],
        }

        if status not in valid_transitions.get(conv.status, []):
            raise ValidationError(
                f"Cannot transition from {conv.status} to {status}"
            )

        # Update
        await self.conversations.update(conv_id, {
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "conversation_status_changed",
            resource_id=conv_id,
            resource_type="conversation",
            details={"status": status},
        )

        return await self.conversations.read(conv_id)

    async def assign_conversation(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
    ) -> Conversation:
        """
        Assign conversation to team member.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            member_id: Member ID to assign to
            
        Returns:
            Updated conversation
        """
        conv = await self.get_conversation(org_id, conv_id)

        # Add as participant if not already
        existing = await self.participants.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })
        if not existing:
            participant = ConversationParticipant(
                conversation_id=conv_id,
                member_id=member_id,
                joined_at=datetime.now(timezone.utc),
            )
            await self.participants.create(participant)

        # Update conversation
        await self.conversations.update(conv_id, {
            "assigned_to": member_id,
            "status": ConversationStatus.ASSIGNED,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "conversation_assigned",
            resource_id=conv_id,
            resource_type="conversation",
            details={"member_id": member_id},
        )

        return await self.conversations.read(conv_id)

    async def unassign_conversation(
        self,
        org_id: str,
        conv_id: str,
    ) -> Conversation:
        """Unassign conversation."""
        conv = await self.get_conversation(org_id, conv_id)

        await self.conversations.update(conv_id, {
            "assigned_to": None,
            "status": ConversationStatus.OPEN,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "conversation_unassigned",
            resource_id=conv_id,
            resource_type="conversation",
        )

        return await self.conversations.read(conv_id)

    async def get_conversation_participants(
        self,
        conv_id: str,
    ) -> list[ConversationParticipant]:
        """Get all participants in conversation."""
        return await self.participants.find({"conversation_id": conv_id})

    async def get_customer_conversations(
        self,
        org_id: str,
        customer_id: str,
    ) -> list[Conversation]:
        """Get all conversations with customer."""
        # Check customer exists
        customer = await self.customers.read(customer_id)
        if not customer or customer.organization_id != org_id:
            raise NotFoundError("Customer", customer_id)

        return await self.conversations.find({
            "organization_id": org_id,
            "customer_id": customer_id,
        })

    async def close_conversation(
        self,
        org_id: str,
        conv_id: str,
        closed_by: str,
        reason: Optional[str] = None,
    ) -> Conversation:
        """Close conversation."""
        conv = await self.get_conversation(org_id, conv_id)

        await self.conversations.update(conv_id, {
            "status": ConversationStatus.CLOSED,
            "closed_at": datetime.now(timezone.utc),
            "closed_by": closed_by,
            "close_reason": reason,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "conversation_closed",
            resource_id=conv_id,
            resource_type="conversation",
            details={"reason": reason},
        )

        return await self.conversations.read(conv_id)

    async def reopen_conversation(
        self,
        org_id: str,
        conv_id: str,
    ) -> Conversation:
        """Reopen closed conversation."""
        conv = await self.get_conversation(org_id, conv_id)

        if conv.status != ConversationStatus.CLOSED:
            raise ValidationError("Can only reopen closed conversations")

        await self.conversations.update(conv_id, {
            "status": ConversationStatus.OPEN,
            "closed_at": None,
            "closed_by": None,
            "close_reason": None,
            "updated_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "conversation_reopened",
            resource_id=conv_id,
            resource_type="conversation",
        )

        return await self.conversations.read(conv_id)
