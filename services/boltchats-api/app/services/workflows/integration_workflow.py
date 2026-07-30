"""
Integration Webhook Workflow

Orchestrates handling webhooks from external providers.

Steps:
1. Validate webhook signature
2. Parse provider payload
3. Route to appropriate handler (message, status, etc)
4. Execute domain workflow (e.g., IncomingMessageWorkflow)
"""

import hmac
import hashlib
from typing import Optional

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.integration import EventType
from app.services.events.workflow_service import Workflow, WorkflowContext
from app.services.integration import IntegrationService


logger = structlog.get_logger()


class IntegrationWorkflow:
    """Workflow for handling provider webhooks"""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        integration_service: IntegrationService,
        workflow_service,  # WorkflowService
        event_bus,
    ):
        self.db = db
        self.integration_service = integration_service
        self.workflow_service = workflow_service
        self.event_bus = event_bus

    def build(self) -> Workflow:
        """Build the workflow."""
        workflow = Workflow("integration_webhook")

        workflow.add_step(
            "validate_webhook",
            self._validate_webhook,
            on_error="stop",
        )
        workflow.add_step(
            "parse_payload",
            self._parse_payload,
            on_error="stop",
        )
        workflow.add_step(
            "determine_event_type",
            self._determine_event_type,
            on_error="stop",
        )
        workflow.add_step(
            "execute_handler",
            self._execute_handler,
            on_error="skip",  # Skip if no handler for event
        )
        workflow.add_step(
            "publish_event",
            self._publish_event,
            on_error="skip",
        )

        return workflow

    async def _validate_webhook(self, ctx: WorkflowContext) -> None:
        """Validate webhook signature from provider."""
        required_fields = [
            "provider",
            "signature",
            "payload",
            "timestamp",
        ]

        for field in required_fields:
            if field not in ctx.data:
                raise ValueError(f"Missing required field: {field}")

        provider = ctx.data["provider"]
        signature = ctx.data["signature"]
        payload = ctx.data["payload"]
        secret = ctx.data.get("secret")

        if not secret:
            logger.warning(
                "webhook_no_secret",
                provider=provider,
            )
            # TODO: Get secret from integration settings
            return

        # Validate signature based on provider
        if provider.lower() == "meta":
            # Meta uses: sha1=HMAC-SHA1(secret, payload_body)
            expected_signature = (
                "sha1="
                + hmac.new(
                    secret.encode(),
                    payload.encode(),
                    hashlib.sha1,
                ).hexdigest()
            )

            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid webhook signature")

        elif provider.lower() == "sendgrid":
            # SendGrid uses: base64(HMAC-SHA256(secret, payload_body))
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).digest()

            import base64
            expected_signature = base64.b64encode(expected_signature).decode()

            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid webhook signature")

        logger.info(
            "webhook_validated",
            provider=provider,
        )

    async def _parse_payload(self, ctx: WorkflowContext) -> dict:
        """Parse provider payload."""
        import json

        provider = ctx.data["provider"]
        payload = ctx.data["payload"]

        try:
            parsed = json.loads(payload) if isinstance(payload, str) else payload
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {str(e)}")

        logger.info(
            "payload_parsed",
            provider=provider,
            keys=list(parsed.keys()),
        )

        return parsed

    async def _determine_event_type(self, ctx: WorkflowContext) -> str:
        """Determine event type from payload."""
        parsed = ctx.get("parse_payload")
        provider = ctx.data["provider"]

        # Map provider event types to domain events
        if provider.lower() == "meta":
            # Meta webhook: check entry[].messaging[].message or delivery
            if "entry" in parsed:
                for entry in parsed.get("entry", []):
                    for msg in entry.get("messaging", []):
                        if "message" in msg:
                            return "incoming_message"
                        elif "delivery" in msg:
                            return "delivery_status"
                        elif "read" in msg:
                            return "read_receipt"

        elif provider.lower() == "sendgrid":
            # SendGrid webhook: check event types
            if "event" in parsed:
                event_type = parsed["event"]
                if event_type == "delivered":
                    return "delivery_status"
                elif event_type == "bounce":
                    return "bounce"

        logger.warning(
            "unknown_event_type",
            provider=provider,
            payload_keys=list(parsed.keys()),
        )

        return "unknown"

    async def _execute_handler(self, ctx: WorkflowContext) -> Optional[str]:
        """Execute handler for event type."""
        event_type = ctx.get("determine_event_type")
        provider = ctx.data["provider"]
        parsed = ctx.get("parse_payload")

        if event_type == "incoming_message":
            # Extract message data and execute IncomingMessageWorkflow
            message_data = self._extract_message_data(provider, parsed)

            workflow_result = await self.workflow_service.execute_workflow(
                org_id=ctx.org_id,
                workflow_name="incoming_message",
                data=message_data,
            )

            return workflow_result.data.get("message_id")

        elif event_type == "delivery_status":
            # Handle delivery status update
            logger.info(
                "delivery_status_received",
                provider=provider,
            )
            return "delivery_handled"

        elif event_type == "read_receipt":
            # Handle read receipt
            logger.info(
                "read_receipt_received",
                provider=provider,
            )
            return "read_receipt_handled"

        else:
            logger.warning(
                "no_handler_for_event",
                event_type=event_type,
            )
            return None

    async def _publish_event(self, ctx: WorkflowContext) -> None:
        """Publish integration event."""
        provider = ctx.data["provider"]
        event_type = ctx.get("determine_event_type")

        await self.event_bus.publish(
            org_id=ctx.org_id,
            event_type=EventType.WEBHOOK_RECEIVED,
            aggregate_id=provider,
            aggregate_type="Integration",
            data={
                "provider": provider,
                "event_type": event_type,
                "handler_result": ctx.get("execute_handler"),
            },
            correlation_id=ctx.workflow_id,
        )

        logger.info(
            "webhook_event_published",
            provider=provider,
            event_type=event_type,
        )

    def _extract_message_data(
        self,
        provider: str,
        payload: dict,
    ) -> dict:
        """Extract message data from provider payload."""
        if provider.lower() == "meta":
            # Meta format: entry[0].messaging[0].message
            try:
                entry = payload["entry"][0]
                messaging = entry["messaging"][0]
                sender = messaging["sender"]
                message = messaging["message"]

                return {
                    "provider": "meta",
                    "provider_user_id": sender["id"],
                    "provider_message_id": message.get("mid"),
                    "channel": "instagram",  # Could be facebook, whatsapp, etc
                    "text": message.get("text", ""),
                    "timestamp": messaging.get("timestamp"),
                    "user_name": sender.get("name"),
                }
            except KeyError as e:
                raise ValueError(f"Invalid Meta payload structure: {str(e)}")

        elif provider.lower() == "sendgrid":
            # SendGrid format: event + email metadata
            try:
                return {
                    "provider": "sendgrid",
                    "provider_user_id": payload.get("from", {}).get("email"),
                    "provider_message_id": payload.get("message_id"),
                    "channel": "email",
                    "text": payload.get("text", ""),
                    "timestamp": payload.get("timestamp"),
                    "user_email": payload.get("from", {}).get("email"),
                    "user_name": payload.get("from", {}).get("name"),
                }
            except KeyError as e:
                raise ValueError(f"Invalid SendGrid payload structure: {str(e)}")

        else:
            raise ValueError(f"Unknown provider: {provider}")
