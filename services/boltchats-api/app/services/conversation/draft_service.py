"""
Draft Service

Draft message management (auto-save)
"""

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import ConversationDraft
from app.repositories import ConversationDraftRepository, ConversationRepository
from app.services.base import BaseService, NotFoundError


class DraftService(BaseService):
    """Manage draft messages"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.drafts = ConversationDraftRepository(db)
        self.conversations = ConversationRepository(db)

    async def save_draft(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
        content: str,
    ) -> ConversationDraft:
        """
        Save or update draft message.
        
        Each member has one draft per conversation (auto-save).
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            member_id: Member saving draft
            content: Draft content
            
        Returns:
            ConversationDraft
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        # Find existing draft for this member
        existing = await self.drafts.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })

        if existing:
            # Update existing draft
            await self.drafts.update(existing.id, {
                "content": content,
                "updated_at": datetime.now(timezone.utc),
            })
            return await self.drafts.read(existing.id)
        else:
            # Create new draft
            draft = ConversationDraft(
                conversation_id=conv_id,
                member_id=member_id,
                content=content,
            )
            draft_id = await self.drafts.create(draft)

            await self.log_action(
                "draft_created",
                resource_id=draft_id,
                resource_type="draft",
            )

            return await self.drafts.read(draft_id)

    async def get_draft(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
    ) -> Optional[ConversationDraft]:
        """
        Get draft for member in conversation.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            member_id: Member
            
        Returns:
            ConversationDraft or None if no draft
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        return await self.drafts.find({
            "conversation_id": conv_id,
            "member_id": member_id,
        })

    async def delete_draft(
        self,
        org_id: str,
        conv_id: str,
        member_id: str,
    ) -> None:
        """
        Delete draft (e.g., after sending message).
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            member_id: Member
        """
        draft = await self.get_draft(org_id, conv_id, member_id)
        
        if draft:
            await self.drafts.delete(draft.id)

            await self.log_action(
                "draft_deleted",
                resource_id=draft.id,
                resource_type="draft",
            )

    async def get_member_drafts(
        self,
        member_id: str,
    ) -> list[ConversationDraft]:
        """Get all drafts for member across conversations."""
        return await self.drafts.find({
            "member_id": member_id,
        })

    async def cleanup_old_drafts(
        self,
        org_id: str,
        days: int = 7,
    ) -> int:
        """
        Delete drafts older than N days (unused).
        
        Args:
            org_id: Organization ID
            days: Age threshold
            
        Returns:
            Number of drafts deleted
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Find old drafts in org's conversations
        # Get all convs in org
        convs = await self.conversations.find({
            "organization_id": org_id,
        })
        conv_ids = [c.id for c in convs]

        old_drafts = await self.drafts.find({
            "conversation_id": {"$in": conv_ids},
            "updated_at": {"$lt": cutoff},
        })

        count = 0
        for draft in old_drafts:
            await self.drafts.delete(draft.id)
            count += 1

        self.logger.info(
            "old_drafts_cleanup",
            org_id=org_id,
            count=count,
            days=days,
        )

        return count
