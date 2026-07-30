"""
Message Service

Message management with threading, editing, deletion
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import Attachment, Message, MessageType
from app.repositories import ConversationRepository, MessageRepository
from app.services.base import BaseService, NotFoundError, ValidationError


class MessageService(BaseService):
    """Manage messages within conversations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db)
        self.messages = MessageRepository(db)
        self.conversations = ConversationRepository(db)

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
        """
        Send message in conversation.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            member_id: Sender member ID
            content: Message content
            message_type: TEXT, IMAGE, FILE, AUDIO, VIDEO
            reply_to_id: Optional message ID to reply to (threading)
            attachments: Optional list of attachments
            
        Returns:
            Message
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        # Validate reply_to if threading
        if reply_to_id:
            reply_msg = await self.messages.read(reply_to_id)
            if not reply_msg or reply_msg.conversation_id != conv_id:
                raise NotFoundError("Message", reply_to_id)

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

        await self.log_action(
            "message_sent",
            resource_id=msg_id,
            resource_type="message",
        )

        return await self.messages.read(msg_id)

    async def get_message(self, org_id: str, conv_id: str, msg_id: str) -> Message:
        """Get message."""
        message = await self.messages.read(msg_id)
        if not message or message.conversation_id != conv_id:
            raise NotFoundError("Message", msg_id)

        # Check conversation belongs to org
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        return message

    async def get_conversation_messages(
        self,
        org_id: str,
        conv_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """
        Get message thread for conversation.
        
        Returns messages in chronological order (oldest first).
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            limit: Max messages to return
            offset: Pagination offset
            
        Returns:
            List of messages
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        return await self.messages.find_by_conversation(conv_id, limit, offset)

    async def get_message_replies(
        self,
        org_id: str,
        conv_id: str,
        msg_id: str,
    ) -> list[Message]:
        """Get all replies to a message (threading)."""
        # Check message exists
        message = await self.get_message(org_id, conv_id, msg_id)

        # Find all messages that reply to this one
        return await self.messages.find({
            "conversation_id": conv_id,
            "reply_to_message_id": msg_id,
        })

    async def edit_message(
        self,
        org_id: str,
        conv_id: str,
        msg_id: str,
        content: str,
        member_id: str,
    ) -> Message:
        """
        Edit message in conversation.
        
        Edit window: 15 minutes after sending.
        Only original sender can edit.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            msg_id: Message ID
            content: New content
            member_id: Member editing (must be original sender)
            
        Returns:
            Updated message
        """
        # Check message exists
        message = await self.get_message(org_id, conv_id, msg_id)

        # Check permission (only original sender)
        if message.member_id != member_id:
            raise ValidationError("Can only edit own messages")

        # Check edit window (15 minutes)
        time_since_created = datetime.now(timezone.utc) - message.created_at
        if time_since_created > timedelta(minutes=15):
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
        """
        Soft delete message (hide from conversation).
        
        Only original sender can delete.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            msg_id: Message ID
            member_id: Member deleting (must be original sender)
        """
        # Check message exists
        message = await self.get_message(org_id, conv_id, msg_id)

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

    async def search_messages(
        self,
        org_id: str,
        conv_id: str,
        query: str,
        limit: int = 20,
    ) -> list[Message]:
        """
        Search messages in conversation.
        
        Args:
            org_id: Organization ID
            conv_id: Conversation ID
            query: Search query
            limit: Max results
            
        Returns:
            List of matching messages
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        return await self.messages.find({
            "conversation_id": conv_id,
            "content": {"$regex": query, "$options": "i"},
        })

    async def get_media_attachments(
        self,
        org_id: str,
        conv_id: str,
    ) -> list[tuple[str, Attachment]]:
        """
        Get all media attachments in conversation.
        
        Returns: List of (message_id, attachment) tuples
        """
        # Check conversation exists
        conv = await self.conversations.read(conv_id)
        if not conv or conv.organization_id != org_id:
            raise NotFoundError("Conversation", conv_id)

        # Get all messages with attachments
        messages = await self.messages.find({
            "conversation_id": conv_id,
            "attachments": {"$exists": True, "$ne": []},
        })

        result = []
        for message in messages:
            for attachment in message.attachments:
                result.append((message.id, attachment))

        return result
