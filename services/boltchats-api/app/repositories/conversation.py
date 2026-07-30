"""
Conversation Domain Repositories

Customers, Conversations, Messages, Labels, Drafts
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import (
    Conversation,
    ConversationDraft,
    ConversationParticipant,
    Customer,
    CustomerIdentity,
    InternalNote,
    Label,
    Message,
)
from app.utils.sparkquark_constants import Collection

from .base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customers"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.CUSTOMERS.value, Customer)

    async def find_by_org(self, organization_id: str) -> list[Customer]:
        """Find all customers in organization"""
        return await self.find_many({"organization_id": organization_id})

    async def find_by_email(self, organization_id: str, email: str) -> Customer | None:
        """Find customer by email"""
        return await self.find({
            "organization_id": organization_id,
            "email": email
        })

    async def search(self, organization_id: str, query: str) -> list[Customer]:
        """Search customers by name or email"""
        return await self.find_many({
            "organization_id": organization_id,
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        })


class CustomerIdentityRepository(BaseRepository[CustomerIdentity]):
    """Repository for customer channel identities"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.CUSTOMER_IDENTITIES.value, CustomerIdentity)

    async def find_by_customer(self, customer_id: str) -> list[CustomerIdentity]:
        """Find all identities for a customer"""
        return await self.find_many({"customer_id": customer_id})

    async def find_by_channel(self, organization_id: str, channel: str, external_id: str) -> CustomerIdentity | None:
        """Find identity by channel and external ID"""
        return await self.find({
            "organization_id": organization_id,
            "channel": channel,
            "external_id": external_id
        })

    async def find_or_get_customer(self, organization_id: str, channel: str, external_id: str) -> str | None:
        """Get customer_id for a channel identity"""
        identity = await self.find_by_channel(organization_id, channel, external_id)
        return identity.customer_id if identity else None


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.CONVERSATIONS.value, Conversation)

    async def find_by_customer(self, organization_id: str, customer_id: str) -> list[Conversation]:
        """Find all conversations with a customer"""
        return await self.find_many({
            "organization_id": organization_id,
            "customer_id": customer_id
        })

    async def find_by_channel(self, organization_id: str, channel: str, external_id: str) -> Conversation | None:
        """Find conversation by channel and external ID"""
        return await self.find({
            "organization_id": organization_id,
            "channel": channel,
            "external_id": external_id
        })

    async def find_inbox(self, organization_id: str, status: str = "open") -> list[Conversation]:
        """Find conversations for inbox (sorted by newest)"""
        return await self.find_many(
            {
                "organization_id": organization_id,
                "status": status
            },
            limit=50  # Inbox limit
        )

    async def find_by_assignee(self, organization_id: str, member_id: str) -> list[Conversation]:
        """Find all conversations assigned to member"""
        return await self.find_many({
            "organization_id": organization_id,
            "assigned_to.member_id": member_id
        })

    async def find_by_label(self, organization_id: str, label_id: str) -> list[Conversation]:
        """Find conversations with label"""
        return await self.find_many({
            "organization_id": organization_id,
            "label_ids": label_id
        })


class ConversationParticipantRepository(BaseRepository[ConversationParticipant]):
    """Repository for conversation participants"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.CONVERSATION_PARTICIPANTS.value, ConversationParticipant)

    async def find_by_conversation(self, conversation_id: str) -> list[ConversationParticipant]:
        """Find all participants in conversation"""
        return await self.find_many({"conversation_id": conversation_id})

    async def is_participant(self, conversation_id: str, member_id: str) -> bool:
        """Check if member is participant"""
        return await self.exists({
            "conversation_id": conversation_id,
            "member_id": member_id
        })

    async def get_unread_count(self, conversation_id: str, member_id: str) -> int:
        """Get unread message count for participant"""
        from motor.motor_asyncio import AsyncIOMotorDatabase
        
        # Get participant record
        participant = await self.find({
            "conversation_id": conversation_id,
            "member_id": member_id
        })
        
        if not participant:
            return 0
            
        # Count messages after last_read_message_id
        from app.repositories.conversation import MessageRepository
        msg_repo = MessageRepository(self.db)
        
        return await msg_repo.count({
            "conversation_id": conversation_id,
            "created_at": {"$gt": participant.last_read_at} if participant.last_read_at else {}
        })


class MessageRepository(BaseRepository[Message]):
    """Repository for messages"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.MESSAGES.value, Message)

    async def find_by_conversation(
        self, conversation_id: str, skip: int = 0, limit: int = 50
    ) -> list[Message]:
        """Find messages in conversation (oldest first)"""
        cursor = self.collection.find({"conversation_id": conversation_id})
        cursor.sort("created_at", 1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model_class.model_validate(doc) for doc in docs]

    async def find_by_thread(self, conversation_id: str, parent_message_id: str) -> list[Message]:
        """Find all replies to a message (thread)"""
        return await self.find_many({
            "conversation_id": conversation_id,
            "reply_to_message_id": parent_message_id
        })

    async def find_by_external_id(self, organization_id: str, external_id: str) -> Message | None:
        """Find message by provider external ID"""
        return await self.find({
            "organization_id": organization_id,
            "external_id": external_id
        })


class InternalNoteRepository(BaseRepository[InternalNote]):
    """Repository for internal notes"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.MESSAGES.value, InternalNote)

    async def find_by_conversation(self, conversation_id: str) -> list[InternalNote]:
        """Find all internal notes in conversation"""
        return await self.find_many({
            "conversation_id": conversation_id,
            "is_internal": True
        })


class LabelRepository(BaseRepository[Label]):
    """Repository for conversation labels"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.LABELS.value, Label)

    async def find_by_org(self, organization_id: str) -> list[Label]:
        """Find all labels in organization"""
        return await self.find_many({"organization_id": organization_id})

    async def find_by_name(self, organization_id: str, name: str) -> Label | None:
        """Find label by name"""
        return await self.find({
            "organization_id": organization_id,
            "name": name
        })


class ConversationDraftRepository(BaseRepository[ConversationDraft]):
    """Repository for message drafts"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, Collection.CONVERSATION_DRAFTS.value, ConversationDraft)

    async def find_by_member(self, conversation_id: str, member_id: str) -> ConversationDraft | None:
        """Find member's draft in conversation"""
        return await self.find({
            "conversation_id": conversation_id,
            "member_id": member_id
        })

    async def find_by_conversation(self, conversation_id: str) -> list[ConversationDraft]:
        """Find all drafts in conversation"""
        return await self.find_many({"conversation_id": conversation_id})
