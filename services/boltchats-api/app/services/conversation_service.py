"""
Conversation Service

Conversation management, customer profiles, messaging
"""

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import (
    Attachment,
    Conversation,
    ConversationChannel,
    ConversationDraft,
    ConversationParticipant,
    ConversationStatus,
    Customer,
    CustomerIdentity,
    Label,
    Message,
    MessageType,
)
from app.repositories import (
    ConversationDraftRepository,
    ConversationParticipantRepository,
    ConversationRepository,
    CustomerIdentityRepository,
    CustomerRepository,
    LabelRepository,
    MessageRepository,
)

from .base import (
    BaseService,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class CustomerService(BaseService):
    """Customer profile management"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.customers = CustomerRepository(db)
        self.customer_identities = CustomerIdentityRepository(db)

    async def create_customer(
        self,
        org_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """Create new customer."""
        customer = Customer(
            organization_id=org_id,
            name=name,
            email=email,
            phone=phone,
        )
        customer_id = await self.customers.create(customer)

        await self.log_action(
            "customer_created",
            resource_id=customer_id,
            resource_type="customer",
        )

        return await self.customers.read(customer_id)

    async def add_customer_identity(
        self,
        org_id: str,
        customer_id: str,
        provider: str,
        external_id: str,
        username: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> CustomerIdentity:
        """Add channel identity to customer (Instagram, WhatsApp, Email, etc)."""
        # Check customer exists
        customer = await self.customers.read(customer_id)
        if not customer or customer.organization_id != org_id:
            raise NotFoundError("Customer", customer_id)

        # Check identity doesn't already exist for this provider
        existing = await self.customer_identities.find_by_provider(
            customer_id, provider
        )
        if existing:
            raise ConflictError(
                f"Customer already has identity on {provider}"
            )

        # Create identity
        identity = CustomerIdentity(
            customer_id=customer_id,
            provider=provider,
            external_id=external_id,
            username=username,
            metadata=metadata or {},
        )
        identity_id = await self.customer_identities.create(identity)

        await self.log_action(
            "customer_identity_added",
            resource_id=identity_id,
            resource_type="customer_identity",
        )

        return await self.customer_identities.read(identity_id)

    async def get_customer(self, org_id: str, customer_id: str) -> Customer:
        """Get customer with all channel identities."""
        customer = await self.customers.read(customer_id)
        if not customer or customer.organization_id != org_id:
            raise NotFoundError("Customer", customer_id)
        return customer

    async def search_customers(
        self,
        org_id: str,
        query: str,
        limit: int = 20,
    ) -> list[Customer]:
        """Search customers by name, email, or phone."""
        return await self.customers.search(org_id, query, limit)


class ConversationService(BaseService):
    """Conversation management, inbox, threading"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.conversations = ConversationRepository(db)
        self.participants = ConversationParticipantRepository(db)
        self.messages = MessageRepository(db)
        self.labels = LabelRepository(db)
        self.drafts = ConversationDraftRepository(db)
        self.customers = CustomerRepository(db)

    # ─── CONVERSATIONS ────────────────────────────────────────────────

    async def create_conversation(
        self,
        org_id: str,
        customer_id: str,
        channel: ConversationChannel,
        assigned_to: Optional[str] = None,
    ) -> Conversation:
        """Create new conversation with customer."""
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

        # Add initial participant
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
        """Get conversations in inbox (open or unresolved)."""
        return await self.conversations.find_inbox(
            org_id, status, limit, offset
        )

    async def update_conversation_status(
        self,
        org_id: str,
        conv_id: str,
        status: ConversationStatus,
    ) -> Conversation:
        """Update conversation status."""
        conv = await self.get_conversation(org_id, conv_id)

        # Validate status transition
        valid_transitions = {
            ConversationStatus.OPEN: [ConversationStatus.ASSIGNED, ConversationStatus.CLOSED],
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
            "conversation_status_updated",
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
        """Assign conversation to team member."""
        conv = await self.get_conversation(org_id, conv_id)

        # Add as participant
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

    # ─── MESSAGES ──────────────────────────────────────────────────────

    async def send_message(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        reply_to_id: Optional[str] = None,
        attachments: Optional[list[Attachment]] = None,
    ) -> Message:
        """Send message in conversation."""
        # Check conversation exists
        conv = await self.get_conversation(org_id, conv_id)

        # Create message
        message = Message(
            conversation_id=conv_id,
            member_id=member_id,
            content=content,
            message_type=message_type,
            reply_to_message_id=reply_to_id,
            attachments=attachments or [],
        )
        msg_id = await self.messages.create(message)

        # Update conversation stats
        await self.conversations.update(conv_id, {
            "last_message_at": datetime.now(timezone.utc),
            "last_message_id": msg_id,
            "message_count": conv.message_count + 1,
            "updated_at": datetime.now(timezone.utc),
        })

        # Update member's last read
        await self.participants.update_last_read(conv_id, member_id, msg_id)

        await self.log_action(
            "message_sent",
            resource_id=msg_id,
            resource_type="message",
        )

        return await self.messages.read(msg_id)

    async def get_conversation_messages(
        self,
        org_id: str,
        conv_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Get message thread for conversation."""
        # Check conversation exists
        await self.get_conversation(org_id, conv_id)

        return await self.messages.find_by_conversation(
            conv_id, limit, offset
        )

    async def edit_message(
        self,
        org_id: str,
        conv_id: str,
        msg_id: str,
        content: str,
        member_id: str,
    ) -> Message:
        """Edit message in conversation."""
        # Check message exists
        message = await self.messages.read(msg_id)
        if not message or message.conversation_id != conv_id:
            raise NotFoundError("Message", msg_id)

        # Check permission
        if message.member_id != member_id:
            raise ValidationError("Can only edit own messages")

        # Check not too old (15 minutes)
        from datetime import timedelta
        if datetime.now(timezone.utc) - message.created_at > timedelta(minutes=15):
            raise ValidationError("Cannot edit messages older than 15 minutes")

        # Update
        await self.messages.update(msg_id, {
            "content": content,
            "edited_at": datetime.now(timezone.utc),
            "edited_by": member_id,
        })

        await self.log_action(
            "message_edited",
            resource_id=msg_id,
            resource_type="message",
        )

        return await self.messages.read(msg_id)

    async def delete_message(
        self,
        org_id: str,
        conv_id: str,
        msg_id: str,
        member_id: str,
    ) -> None:
        """Delete (hide) message in conversation."""
        # Check message exists
        message = await self.messages.read(msg_id)
        if not message or message.conversation_id != conv_id:
            raise NotFoundError("Message", msg_id)

        # Check permission
        if message.member_id != member_id:
            raise ValidationError("Can only delete own messages")

        # Soft delete
        await self.messages.update(msg_id, {
            "deleted_by": member_id,
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "message_deleted",
            resource_id=msg_id,
            resource_type="message",
        )

    # ─── LABELS ───────────────────────────────────────────────────────

    async def create_label(
        self,
        org_id: str,
        name: str,
        color: str = "#000000",
    ) -> Label:
        """Create label for conversations."""
        label = Label(
            organization_id=org_id,
            name=name,
            color=color,
        )
        label_id = await self.labels.create(label)

        await self.log_action(
            "label_created",
            resource_id=label_id,
            resource_type="label",
        )

        return await self.labels.read(label_id)

    async def add_label_to_conversation(
        self,
        org_id: str,
        conv_id: str,
        label_id: str,
    ) -> Conversation:
        """Add label to conversation."""
        # Check conversation exists
        conv = await self.get_conversation(org_id, conv_id)

        # Check label exists in org
        label = await self.labels.read(label_id)
        if not label or label.organization_id != org_id:
            raise NotFoundError("Label", label_id)

        # Add label if not already there
        if label_id not in conv.label_ids:
            conv.label_ids.append(label_id)
            await self.conversations.update(conv_id, {
                "label_ids": conv.label_ids,
                "updated_at": datetime.now(timezone.utc),
            })

        await self.log_action(
            "label_added_to_conversation",
            resource_id=conv_id,
            resource_type="conversation",
        )

        return await self.conversations.read(conv_id)

    # ─── DRAFTS ────────────────────────────────────────────────────────

    async def save_draft(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
        content: str,
    ) -> ConversationDraft:
        """Save draft message."""
        # Check conversation exists
        await self.get_conversation(org_id, conv_id)

        # Find existing draft for this member
        existing = await self.drafts.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })

        if existing:
            # Update existing
            await self.drafts.update(existing.id, {
                "content": content,
                "updated_at": datetime.now(timezone.utc),
            })
            return await self.drafts.read(existing.id)
        else:
            # Create new
            draft = ConversationDraft(
                conversation_id=conv_id,
                member_id=member_id,
                content=content,
            )
            draft_id = await self.drafts.create(draft)
            return await self.drafts.read(draft_id)

    async def get_draft(
        self,
        conv_id: str,
        member_id: str,
    ) -> Optional[ConversationDraft]:
        """Get draft for member in conversation."""
        draft = await self.drafts.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })
        return draft

    async def delete_draft(
        self,
        conv_id: str,
        member_id: str,
    ) -> None:
        """Delete draft."""
        draft = await self.drafts.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })
        if draft:
            await self.drafts.delete(draft.id)
