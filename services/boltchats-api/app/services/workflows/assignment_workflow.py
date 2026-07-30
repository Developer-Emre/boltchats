"""
Assignment Workflow

Orchestrates assigning a conversation to a team member.

Steps:
1. Validate assignment request
2. Check member permissions
3. Add member as conversation participant
4. Update conversation status to ASSIGNED
5. Publish event for notifications
"""

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import ConversationStatus
from app.models.integration import EventType
from app.services.conversation import ConversationService
from app.services.events.workflow_service import Workflow, WorkflowContext
from app.services.organization import MemberService
from app.services.security import PermissionService


logger = structlog.get_logger()


class AssignmentWorkflow:
    """Workflow for assigning conversations to team members"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        conversation_service: ConversationService,
        member_service: MemberService,
        permission_service: PermissionService,
        event_bus,
    ):
        self.db = db
        self.conversation_service = conversation_service
        self.member_service = member_service
        self.permission_service = permission_service
        self.event_bus = event_bus

    def build(self) -> Workflow:
        """Build the workflow."""
        workflow = Workflow("assignment")

        workflow.add_step(
            "validate",
            self._validate_assignment,
            on_error="stop",
        )
        workflow.add_step(
            "check_permissions",
            self._check_permissions,
            on_error="stop",
        )
        workflow.add_step(
            "add_participant",
            self._add_participant,
            on_error="stop",
        )
        workflow.add_step(
            "update_conversation",
            self._update_conversation,
            on_error="stop",
        )
        workflow.add_step(
            "publish_event",
            self._publish_event,
            on_error="skip",
        )

        return workflow

    async def _validate_assignment(self, ctx: WorkflowContext) -> None:
        """Validate assignment request."""
        required_fields = [
            "conversation_id",
            "assigned_to_member_id",
            "assigned_by_member_id",
        ]

        for field in required_fields:
            if field not in ctx.data:
                raise ValueError(f"Missing required field: {field}")

        # Validate conversation exists
        conversation = await self.conversation_service.get_conversation(
            org_id=ctx.org_id,
            conversation_id=ctx.data["conversation_id"],
        )

        if not conversation:
            raise ValueError(
                f"Conversation not found: {ctx.data['conversation_id']}"
            )

        # Check if already assigned
        if conversation.status == ConversationStatus.ASSIGNED:
            if conversation.assigned_to == ctx.data["assigned_to_member_id"]:
                raise ValueError("Conversation already assigned to this member")

        logger.info(
            "assignment_validated",
            conversation_id=ctx.data["conversation_id"],
        )

    async def _check_permissions(self, ctx: WorkflowContext) -> None:
        """Check if assignor has permission to assign."""
        assigning_member_id = ctx.data["assigned_by_member_id"]

        # Check permission
        has_permission = await self.permission_service.has_permission(
            org_id=ctx.org_id,
            member_id=assigning_member_id,
            permission="CONVERSATION_ASSIGN",
        )

        if not has_permission:
            raise PermissionError(
                "Member does not have permission to assign conversations"
            )

        logger.info(
            "assignment_permissions_checked",
            member_id=assigning_member_id,
        )

    async def _add_participant(self, ctx: WorkflowContext) -> str:
        """Add assigned member as participant."""
        conversation_id = ctx.data["conversation_id"]
        member_id = ctx.data["assigned_to_member_id"]

        # Add member as participant
        participant = await self.conversation_service.add_participant(
            org_id=ctx.org_id,
            conversation_id=conversation_id,
            member_id=member_id,
        )

        logger.info(
            "participant_added",
            conversation_id=conversation_id,
            member_id=member_id,
        )

        return participant.id

    async def _update_conversation(self, ctx: WorkflowContext) -> None:
        """Update conversation status to ASSIGNED."""
        conversation_id = ctx.data["conversation_id"]
        member_id = ctx.data["assigned_to_member_id"]

        await self.conversation_service.update_conversation(
            org_id=ctx.org_id,
            conversation_id=conversation_id,
            data={
                "status": ConversationStatus.ASSIGNED,
                "assigned_to": member_id,
                "assigned_at": ctx.data.get("assigned_at"),
            },
        )

        logger.info(
            "conversation_assigned",
            conversation_id=conversation_id,
            member_id=member_id,
        )

    async def _publish_event(self, ctx: WorkflowContext) -> None:
        """Publish event for notifications."""
        conversation_id = ctx.data["conversation_id"]
        member_id = ctx.data["assigned_to_member_id"]

        await self.event_bus.publish(
            org_id=ctx.org_id,
            event_type=EventType.CONVERSATION_ASSIGNED,
            aggregate_id=conversation_id,
            aggregate_type="Conversation",
            data={
                "conversation_id": conversation_id,
                "assigned_to": member_id,
                "assigned_by": ctx.data["assigned_by_member_id"],
            },
            correlation_id=ctx.workflow_id,
        )

        logger.info(
            "assignment_event_published",
            conversation_id=conversation_id,
            event_type=EventType.CONVERSATION_ASSIGNED,
        )
