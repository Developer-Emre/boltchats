"""
Incoming Message Workflow

Orchestrates the full journey of an incoming message from external provider.

Steps:
1. Validate message from provider
2. Get or create customer identity
3. Get or create conversation
4. Add conversation participant
5. Create message in conversation
6. Update conversation metadata (last_message, count)
7. Publish event for notifications
"""

from typing import Optional

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationStatus,
    Message,
    MessageType,
)
from app.models.integration import EventType
from app.services.conversation import (
    ConversationService,
    CustomerService,
    MessageService,
)
from app.services.events.workflow_service import Workflow, WorkflowContext
from app.services.integration import IntegrationService


logger = structlog.get_logger()


class IncomingMessageWorkflow:
    """Workflow for processing incoming messages from external channels"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        customer_service: CustomerService,
        conversation_service: ConversationService,
        message_service: MessageService,
        integration_service: IntegrationService,
        event_bus,
    ):
        self.db = db
        self.customer_service = customer_service
        self.conversation_service = conversation_service
        self.message_service = message_service
        self.integration_service = integration_service
        self.event_bus = event_bus

    def build(self) -> Workflow:
        """Build the workflow."""
        workflow = Workflow("incoming_message")

        workflow.add_step(
            "validate",
            self._validate_message,
            on_error="stop",
        )
        workflow.add_step(
            "get_or_create_customer",
            self._get_or_create_customer,
            on_error="stop",
        )
        workflow.add_step(
            "get_or_create_conversation",
            self._get_or_create_conversation,
            on_error="stop",
        )
        workflow.add_step(
            "add_participant",
            self._add_participant,
            on_error="skip",  # Skip if participant already exists
        )
        workflow.add_step(
            "create_message",
            self._create_message,
            on_error="stop",
        )
        workflow.add_step(
            "update_conversation_metadata",
            self._update_conversation_metadata,
            on_error="skip",
        )
        workflow.add_step(
            "publish_event",
            self._publish_event,
            on_error="skip",  # Notification failure shouldn't block
        )

        return workflow

    async def _validate_message(self, ctx: WorkflowContext) -> None:
        """Validate message from provider."""
        required_fields = [
            "provider",
            "provider_user_id",
            "provider_message_id",
            "channel",
            "text",
            "timestamp",
        ]

        for field in required_fields:
            if field not in ctx.data:
                raise ValueError(f"Missing required field: {field}")

        logger.info(
            "incoming_message_validated",
            provider=ctx.data.get("provider"),
            channel=ctx.data.get("channel"),
        )

    async def _get_or_create_customer(self, ctx: WorkflowContext) -> str:
        """Get or create customer from provider identity."""
        provider = ctx.data["provider"]
        provider_user_id = ctx.data["provider_user_id"]
        channel = ctx.data["channel"]

        # Try to find existing customer
        customer = await self.customer_service.get_customer_by_provider_id(
            org_id=ctx.org_id,
            provider=provider,
            provider_user_id=provider_user_id,
        )

        if customer:
            logger.info(
                "customer_found",
                customer_id=customer.id,
                provider=provider,
            )
            return customer.id

        # Create new customer
        customer_data = {
            "organization_id": ctx.org_id,
            "name": ctx.data.get("user_name", f"Customer {provider_user_id}"),
            "email": ctx.data.get("user_email"),
            "phone": ctx.data.get("user_phone"),
        }

        customer = await self.customer_service.create_customer(
            org_id=ctx.org_id,
            **customer_data,
        )

        # Add provider identity
        await self.customer_service.add_customer_identity(
            org_id=ctx.org_id,
            customer_id=customer.id,
            provider=provider,
            external_id=provider_user_id,
            username=ctx.data.get("user_username", provider_user_id),
            metadata={
                "channel": channel,
                "avatar": ctx.data.get("user_avatar"),
                "first_seen": ctx.data.get("timestamp"),
            },
        )

        logger.info(
            "customer_created",
            customer_id=customer.id,
            provider=provider,
        )

        return customer.id

    async def _get_or_create_conversation(self, ctx: WorkflowContext) -> str:
        """Get or create conversation for this customer + channel."""
        customer_id = ctx.get("get_or_create_customer")
        provider = ctx.data["provider"]
        channel = ctx.data["channel"]

        # Try to find open conversation
        conversation = await self.conversation_service.find_conversation_by_customer(
            org_id=ctx.org_id,
            customer_id=customer_id,
            channel=channel,
            status=ConversationStatus.OPEN,
        )

        if conversation:
            logger.info(
                "conversation_found",
                conversation_id=conversation.id,
                customer_id=customer_id,
            )
            return conversation.id

        # Create new conversation
        conversation = await self.conversation_service.create_conversation(
            org_id=ctx.org_id,
            customer_id=customer_id,
            channel=channel,
            subject=ctx.data.get("subject", f"Message from {channel}"),
            status=ConversationStatus.OPEN,
            metadata={
                "provider": provider,
                "initiated_by": "customer",
                "first_message_at": ctx.data.get("timestamp"),
            },
        )

        logger.info(
            "conversation_created",
            conversation_id=conversation.id,
            customer_id=customer_id,
        )

        return conversation.id

    async def _add_participant(self, ctx: WorkflowContext) -> Optional[str]:
        """Add customer as conversation participant."""
        conversation_id = ctx.get("get_or_create_conversation")
        customer_id = ctx.get("get_or_create_customer")

        # In this context, customer is the participant (not a member)
        # This step could be extended to track customer participation

        logger.debug(
            "participant_added",
            conversation_id=conversation_id,
            customer_id=customer_id,
        )

        return None

    async def _create_message(self, ctx: WorkflowContext) -> str:
        """Create message in conversation."""
        conversation_id = ctx.get("get_or_create_conversation")
        customer_id = ctx.get("get_or_create_customer")

        message = await self.message_service.send_message(
            org_id=ctx.org_id,
            conversation_id=conversation_id,
            sender_id=customer_id,
            text=ctx.data["text"],
            message_type=MessageType.TEXT,
            metadata={
                "provider": ctx.data["provider"],
                "channel": ctx.data["channel"],
                "provider_message_id": ctx.data["provider_message_id"],
                "timestamp": ctx.data["timestamp"],
            },
        )

        logger.info(
            "message_created",
            message_id=message.id,
            conversation_id=conversation_id,
        )

        return message.id

    async def _update_conversation_metadata(self, ctx: WorkflowContext) -> None:
        """Update conversation metadata."""
        conversation_id = ctx.get("get_or_create_conversation")
        message_id = ctx.get("create_message")

        # Update last_message info
        await self.conversation_service.update_conversation(
            org_id=ctx.org_id,
            conversation_id=conversation_id,
            data={
                "last_message_id": message_id,
                "last_message_at": ctx.data["timestamp"],
            },
        )

        logger.debug(
            "conversation_metadata_updated",
            conversation_id=conversation_id,
        )

    async def _publish_event(self, ctx: WorkflowContext) -> None:
        """Publish event for notifications."""
        conversation_id = ctx.get("get_or_create_conversation")
        message_id = ctx.get("create_message")

        await self.event_bus.publish(
            org_id=ctx.org_id,
            event_type=EventType.MESSAGE_RECEIVED,
            aggregate_id=message_id,
            aggregate_type="Message",
            data={
                "conversation_id": conversation_id,
                "message_id": message_id,
                "provider": ctx.data["provider"],
                "channel": ctx.data["channel"],
            },
            correlation_id=ctx.workflow_id,
        )

        logger.info(
            "incoming_message_event_published",
            message_id=message_id,
            event_type=EventType.MESSAGE_RECEIVED,
        )
