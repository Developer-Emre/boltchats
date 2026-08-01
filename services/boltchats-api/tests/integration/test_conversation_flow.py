"""
Integration tests for conversation and messaging flow

Tests: Conversation creation, messaging, message editing/deletion, conversation state
"""

import pytest
from datetime import datetime, timezone

from app.services import ConversationService, MessageService, CustomerService


@pytest.mark.asyncio
class TestConversationFlow:
    """End-to-end conversation flow tests"""

    async def test_create_conversation_with_customer(
        self,
        mongodb,
        org_id: str,
    ):
        """Test creating conversation with customer"""
        customer_service = CustomerService(mongodb)
        conversation_service = ConversationService(mongodb)

        # Create customer first
        customer = await customer_service.create_customer(
            organization_id=org_id,
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
        )

        # Create conversation
        conversation = await conversation_service.create_conversation(
            org_id=org_id,
            customer_id=customer["id"],
            channel="email",
            subject="Support Request",
        )

        assert conversation is not None
        assert conversation["customer_id"] == customer["id"]
        assert conversation["channel"] == "email"
        assert conversation["status"] == "open"

    async def test_send_message_flow(
        self,
        mongodb,
        org_id: str,
        member_id: str,
        conversation_id: str,
    ):
        """Test sending messages in conversation"""
        message_service = MessageService(mongodb)

        # Send first message
        message1 = await message_service.send_message(
            org_id=org_id,
            conversation_id=conversation_id,
            sender_id=member_id,
            text="Hello, this is the first message",
        )

        assert message1 is not None
        assert message1["text"] == "Hello, this is the first message"
        assert message1["sender_id"] == member_id
        assert message1["conversation_id"] == conversation_id

        # Send second message
        message2 = await message_service.send_message(
            org_id=org_id,
            conversation_id=conversation_id,
            sender_id=member_id,
            text="This is the second message",
        )

        assert message2 is not None
        assert message2["sequence_order"] > message1["sequence_order"]

    async def test_message_threading_with_reply(
        self,
        mongodb,
        org_id: str,
        member_id: str,
        conversation_id: str,
        message_id: str,
    ):
        """Test replying to a message (threading)"""
        message_service = MessageService(mongodb)

        # Send reply to message
        reply = await message_service.send_message(
            org_id=org_id,
            conversation_id=conversation_id,
            sender_id=member_id,
            text="This is a reply",
            reply_to_message_id=message_id,
        )

        assert reply is not None
        assert reply["reply_to_message_id"] == message_id

        # Get thread
        thread = await message_service.get_message_thread(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )

        assert len(thread) >= 1

    async def test_edit_message_flow(
        self,
        mongodb,
        org_id: str,
        member_id: str,
        conversation_id: str,
        message_id: str,
    ):
        """Test editing a message"""
        message_service = MessageService(mongodb)

        # Edit message
        edited = await message_service.edit_message(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            text="Updated message text",
            edited_by=member_id,
        )

        assert edited is not None
        assert edited["text"] == "Updated message text"
        assert edited["edited_by"] == member_id
        assert edited["edited_at"] is not None

    async def test_delete_message_flow(
        self,
        mongodb,
        org_id: str,
        member_id: str,
        conversation_id: str,
        message_id: str,
    ):
        """Test soft deleting a message"""
        message_service = MessageService(mongodb)

        # Delete message
        await message_service.delete_message(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
            deleted_by=member_id,
        )

        # Get message - should still exist but marked as deleted
        message = await message_service.get_message(
            org_id=org_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )

        # Message should show as deleted
        assert message is not None
        assert message.get("deleted_at") is not None
        assert message.get("deleted_by") == member_id

    async def test_conversation_status_transitions(
        self,
        mongodb,
        org_id: str,
        conversation_id: str,
    ):
        """Test conversation status transitions"""
        conversation_service = ConversationService(mongodb)

        # Create conversation (initial status: open)
        conversation = await conversation_service.get_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert conversation["status"] == "open"

        # Assign conversation
        await conversation_service.assign_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
            assigned_to="member-assign-test",
        )

        assigned_conv = await conversation_service.get_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert assigned_conv["assigned_to"] is not None

        # Close conversation
        await conversation_service.update_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
            data={"status": "closed"},
        )

        closed_conv = await conversation_service.get_conversation(
            org_id=org_id,
            conversation_id=conversation_id,
        )

        assert closed_conv["status"] == "closed"

    async def test_conversation_with_attachments(
        self,
        mongodb,
        org_id: str,
        member_id: str,
        conversation_id: str,
    ):
        """Test sending message with attachments"""
        message_service = MessageService(mongodb)

        attachments = [
            {
                "id": "attach-1",
                "url": "https://example.com/file1.pdf",
                "file_name": "document.pdf",
                "file_size": 1024,
            },
        ]

        message = await message_service.send_message(
            org_id=org_id,
            conversation_id=conversation_id,
            sender_id=member_id,
            text="See attached file",
            attachments=attachments,
        )

        assert message is not None
        assert len(message.get("attachments", [])) > 0

    async def test_message_search_in_conversation(
        self,
        mongodb,
        org_id: str,
        conversation_id: str,
    ):
        """Test searching messages in conversation"""
        message_service = MessageService(mongodb)

        # Search for messages containing specific text
        results = await message_service.search_messages(
            org_id=org_id,
            conversation_id=conversation_id,
            query="test",
            limit=10,
        )

        assert isinstance(results, list)
