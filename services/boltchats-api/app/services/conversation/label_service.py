"""
Label Service

Label management for organizing conversations
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import Label
from app.repositories import ConversationRepository, LabelRepository
from app.services.base import BaseService, ConflictError, NotFoundError


class LabelService(BaseService):
    """Manage labels for organizing conversations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.labels = LabelRepository(db)
        self.conversations = ConversationRepository(db)

    async def create_label(
        self,
        org_id: str,
        name: str,
        color: str = "#000000",
        description: str = "",
    ) -> Label:
        """
        Create label for conversations.
        
        Args:
            org_id: Organization ID
            name: Label name (Urgent, VIP, Follow-up, etc)
            color: Hex color code
            description: Label description
            
        Returns:
            Label
        """
        # Check name unique in org
        existing = await self.labels.find({
            "organization_id": org_id,
            "name": name,
        })
        if existing:
            raise ConflictError(f"Label '{name}' already exists")

        label = Label(
            organization_id=org_id,
            name=name,
            color=color,
            description=description,
        )
        label_id = await self.labels.create(label)

        await self.log_action(
            "label_created",
            resource_id=label_id,
            resource_type="label",
            details={"name": name},
        )

        return await self.labels.read(label_id)

    async def get_label(self, org_id: str, label_id: str) -> Label:
        """Get label."""
        label = await self.labels.read(label_id)
        if not label or label.organization_id != org_id:
            raise NotFoundError("Label", label_id)
        return label

    async def get_labels(self, org_id: str) -> list[Label]:
        """Get all labels in organization."""
        return await self.labels.find({
            "organization_id": org_id,
        })

    async def update_label(
        self,
        org_id: str,
        label_id: str,
        name: str | None = None,
        color: str | None = None,
        description: str | None = None,
    ) -> Label:
        """Update label."""
        label = await self.get_label(org_id, label_id)

        update_data = {}
        if name:
            # Check new name unique
            existing = await self.labels.find({
                "organization_id": org_id,
                "name": name,
            })
            if existing and existing.id != label_id:
                raise ConflictError(f"Label '{name}' already exists")
            update_data["name"] = name

        if color:
            update_data["color"] = color

        if description is not None:
            update_data["description"] = description

        update_data["updated_at"] = datetime.now(timezone.utc)

        await self.labels.update(label_id, update_data)
        return await self.labels.read(label_id)

    async def delete_label(self, org_id: str, label_id: str) -> None:
        """Delete label (soft delete)."""
        label = await self.get_label(org_id, label_id)

        await self.labels.update(label_id, {
            "deleted_at": datetime.now(timezone.utc),
        })

        await self.log_action(
            "label_deleted",
            resource_id=label_id,
            resource_type="label",
        )

    # ─── LABEL ASSOCIATIONS ────────────────────────────────────────────

    async def add_label_to_conversation(
        self,
        org_id: str,
        conv_id: str,
        label_id: str,
    ) -> None:
        """
        Add label to conversation.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            label_id: Label ID
        """
        # Check label exists in org
        label = await self.get_label(org_id, label_id)

        # Check conversation exists in org
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

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
                details={"label_id": label_id},
            )

    async def remove_label_from_conversation(
        self,
        org_id: str,
        conv_id: str,
        label_id: str,
    ) -> None:
        """Remove label from conversation."""
        # Check label exists
        label = await self.get_label(org_id, label_id)

        # Check conversation exists in org
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        # Remove label if present
        if label_id in conv.label_ids:
            conv.label_ids.remove(label_id)
            await self.conversations.update(conv_id, {
                "label_ids": conv.label_ids,
                "updated_at": datetime.now(timezone.utc),
            })

            await self.log_action(
                "label_removed_from_conversation",
                resource_id=conv_id,
                resource_type="conversation",
                details={"label_id": label_id},
            )

    async def get_conversations_by_label(
        self,
        org_id: str,
        label_id: str,
        limit: int = 20,
    ) -> list[Label]:
        """Get all conversations with label."""
        # Check label exists
        label = await self.get_label(org_id, label_id)

        conversations = await self.conversations.find({
            "organization_id": org_id,
            "label_ids": {"$in": [label_id]},
        })

        return conversations[:limit]

    async def get_conversation_labels(
        self,
        org_id: str,
        conv_id: str,
    ) -> list[Label]:
        """Get all labels for conversation."""
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        if not conv.label_ids:
            return []

        # Get label objects
        labels = []
        for label_id in conv.label_ids:
            label = await self.labels.read(label_id)
            if label:
                labels.append(label)

        return labels

    async def bulk_add_label(
        self,
        org_id: str,
        conv_ids: list[str],
        label_id: str,
    ) -> int:
        """
        Add label to multiple conversations.
        
        Args:
            org_id: Organization ID
            conv_ids: List of conversation IDs
            label_id: Label ID
            
        Returns:
            Number of conversations updated
        """
        # Check label exists
        label = await self.get_label(org_id, label_id)

        count = 0
        for conv_id in conv_ids:
            try:
                await self.add_label_to_conversation(org_id, conv_id, label_id)
                count += 1
            except NotFoundError:
                # Skip conversations that don't exist
                pass

        self.logger.info(
            "bulk_label_add",
            label_id=label_id,
            count=count,
        )

        return count
