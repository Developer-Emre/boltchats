"""
Unit tests for Conversation Service

Tests: create conversation, send message, edit/delete message, labels
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services import (
    ConversationService,
    CustomerService,
    MessageService,
    ValidationError,
)


@pytest.mark.asyncio
class TestConversationService:
    """Conversation service tests"""

    async def test_create_conversation_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        customer_id: str,
        test_conversation_data: dict,
    ):
        """Test creating a conversation"""
        service = ConversationService(mock_db, mock_redis)

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=test_conversation_data["id"])
        )
        mock_collection.find_one = AsyncMock(return_value=test_conversation_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.create_conversation(
            org_id=org_id,
            customer_id=customer_id,
            channel="email",
            subject="Test conversation",
        )

        assert result is not None
        assert result["customer_id"] == customer_id
        assert result["channel"] == "email"

    async def test_get_conversation_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        test_conversation_data: dict,
    ):
        """Test getting a conversation"""
        service = ConversationService(mock_db, mock_redis)

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=test_conversation_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.get_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert result is not None
        assert result["id"] == conversation_id

    async def test_get_conversation_not_found(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
    ):
        """Test getting a conversation - not found"""
        service = ConversationService(mock_db, mock_redis)

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.get_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert result is None

    async def test_update_conversation(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        test_conversation_data: dict,
    ):
        """Test updating a conversation"""
        service = ConversationService(mock_db, mock_redis)

        updated_data = test_conversation_data.copy()
        updated_data["status"] = "closed"

        mock_collection = MagicMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=updated_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.update_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
            data={"status": "closed"},
        )

        assert result is not None
        assert result["status"] == "closed"


@pytest.mark.asyncio
class TestMessageService:
    """Message service tests"""

    async def test_send_message_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        member_id: str,
        test_message_data: dict,
    ):
        """Test sending a message"""
        service = MessageService(mock_db, mock_redis)

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=test_message_data["id"])
        )
        mock_collection.find_one = AsyncMock(return_value=test_message_data)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.send_message(
            org_id=org_id,
            conversation_id=conversation_id,
            sender_id=member_id,
            text="Test message",
        )

        assert result is not None
        assert result["text"] == "Test message"
        assert result["conversation_id"] == conversation_id

    async def test_send_message_empty_text(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        member_id: str,
    ):
        """Test sending a message with empty text"""
        service = MessageService(mock_db, mock_redis)

        with pytest.raises(ValidationError):
            await service.send_message(
                org_id=org_id,
                conversation_id=conversation_id,
                sender_id=member_id,
                text="",
            )

    async def test_edit_message_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        message_id: str,
        member_id: str,
        test_message_data: dict,
    ):
        """Test editing a message"""
        service = MessageService(mock_db, mock_redis)

        updated_message = test_message_data.copy()
        updated_message["text"] = "Updated message text"
        updated_message["edited_by"] = member_id

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=updated_message)
        mock_collection.update_one = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.edit_message(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            text="Updated message text",
            edited_by=member_id,
        )

        assert result is not None
        assert result["text"] == "Updated message text"

    async def test_delete_message_success(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        message_id: str,
        member_id: str,
        test_message_data: dict,
    ):
        """Test deleting a message (soft delete)"""
        service = MessageService(mock_db, mock_redis)

        deleted_message = test_message_data.copy()
        deleted_message["deleted_at"] = datetime.now(timezone.utc)
        deleted_message["deleted_by"] = member_id

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=deleted_message)
        mock_collection.update_one = AsyncMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        await service.delete_message(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            deleted_by=member_id,
        )

        # Verify update was called
        assert mock_collection.update_one.called

    async def test_list_messages(
        self,
        mock_db: MagicMock,
        mock_redis,
        org_id: str,
        conversation_id: str,
        test_message_data: dict,
    ):
        """Test listing messages in conversation"""
        service = MessageService(mock_db, mock_redis)

        mock_collection = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [test_message_data]
        mock_collection.find.return_value = mock_cursor
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        result = await service.list_messages(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert isinstance(result, list)
        assert len(result) > 0
