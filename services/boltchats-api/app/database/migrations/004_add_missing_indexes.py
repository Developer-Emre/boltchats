"""
Migration 004: Add missing indexes for dashboard queries and soft deletes
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.migrations import Migration
from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class AddMissingIndexesMigration(Migration):
    """Add missing indexes for common dashboard and reporting queries"""

    version = 4
    name = "add_missing_indexes"
    description = "Add indexes for dashboard queries, soft deletes, and reporting"

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Create missing indexes"""
        # Conversation: organization_id + updated_at DESC (for dashboard sorting)
        await db[Collection.CONVERSATIONS].create_index(
            [("organization_id", 1), ("updated_at", -1)]
        )
        logger.info("index_created", collection=Collection.CONVERSATIONS, fields="org+updated_at_desc")

        # Message: conversation_id + deleted_at + created_at
        # For queries that filter soft-deleted messages
        await db[Collection.MESSAGES].create_index(
            [("conversation_id", 1), ("deleted_at", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.MESSAGES, fields="conv+deleted_at+created_at")

        # Message: sender_id + created_at (for user message history)
        await db[Collection.MESSAGES].create_index(
            [("sender_id", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.MESSAGES, fields="sender+created_at")

        # Notification: recipient_id + read + created_at
        # For unread badge and notification list
        await db[Collection.NOTIFICATIONS].create_index(
            [("recipient_id", 1), ("read", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.NOTIFICATIONS, fields="recipient+read+created_at")

        # Notification: organization_id + recipient_id + read
        await db[Collection.NOTIFICATIONS].create_index(
            [("organization_id", 1), ("recipient_id", 1), ("read", 1)]
        )
        logger.info("index_created", collection=Collection.NOTIFICATIONS, fields="org+recipient+read")

        # Event: aggregate_id + sequence (for event replay)
        await db[Collection.EVENTS].create_index(
            [("aggregate_id", 1), ("sequence", 1)]
        )
        logger.info("index_created", collection=Collection.EVENTS, fields="aggregate_id+sequence")

        # Event: organization_id + aggregate_type + created_at
        await db[Collection.EVENTS].create_index(
            [("organization_id", 1), ("aggregate_type", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.EVENTS, fields="org+aggregate_type+created_at")

        # Audit log: resource_id + action + created_at (for audit trails)
        await db[Collection.AUDIT_LOGS].create_index(
            [("resource_id", 1), ("action", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.AUDIT_LOGS, fields="resource+action+created_at")

        # Audit log: actor_id + created_at (for user activity)
        await db[Collection.AUDIT_LOGS].create_index(
            [("actor_id", 1), ("created_at", -1)]
        )
        logger.info("index_created", collection=Collection.AUDIT_LOGS, fields="actor+created_at")

        # Customer: organization_id + last_contact_at (for activity sorting)
        await db[Collection.CUSTOMERS].create_index(
            [("organization_id", 1), ("last_contact_at", -1)]
        )
        logger.info("index_created", collection=Collection.CUSTOMERS, fields="org+last_contact_at")

        # Conversation participant: member_id + conversation_id
        await db[Collection.CONVERSATION_PARTICIPANTS].create_index(
            [("member_id", 1), ("conversation_id", 1)]
        )
        logger.info("index_created", collection=Collection.CONVERSATION_PARTICIPANTS, fields="member+conv")

        # Role: organization_id + name (for permission lookups)
        await db[Collection.ROLES].create_index(
            [("organization_id", 1), ("name", 1)]
        )
        logger.info("index_created", collection=Collection.ROLES, fields="org+name")

        # Integration: organization_id + status (for active integrations)
        await db[Collection.INTEGRATIONS].create_index(
            [("organization_id", 1), ("status", 1)]
        )
        logger.info("index_created", collection=Collection.INTEGRATIONS, fields="org+status")

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Remove added indexes"""
        index_specs = [
            (Collection.CONVERSATIONS, [("organization_id", 1), ("updated_at", -1)]),
            (Collection.MESSAGES, [("conversation_id", 1), ("deleted_at", 1), ("created_at", -1)]),
            (Collection.MESSAGES, [("sender_id", 1), ("created_at", -1)]),
            (Collection.NOTIFICATIONS, [("recipient_id", 1), ("read", 1), ("created_at", -1)]),
            (Collection.NOTIFICATIONS, [("organization_id", 1), ("recipient_id", 1), ("read", 1)]),
            (Collection.EVENTS, [("aggregate_id", 1), ("sequence", 1)]),
            (Collection.EVENTS, [("organization_id", 1), ("aggregate_type", 1), ("created_at", -1)]),
            (Collection.AUDIT_LOGS, [("resource_id", 1), ("action", 1), ("created_at", -1)]),
            (Collection.AUDIT_LOGS, [("actor_id", 1), ("created_at", -1)]),
            (Collection.CUSTOMERS, [("organization_id", 1), ("last_contact_at", -1)]),
            (Collection.CONVERSATION_PARTICIPANTS, [("member_id", 1), ("conversation_id", 1)]),
            (Collection.ROLES, [("organization_id", 1), ("name", 1)]),
            (Collection.INTEGRATIONS, [("organization_id", 1), ("status", 1)]),
        ]

        for collection_name, index_spec in index_specs:
            try:
                # Build index name from spec
                index_name = "_".join(
                    f"{field}_{direction}" for field, direction in index_spec
                )
                await db[collection_name].drop_index(index_name)
                logger.info("index_dropped", collection=collection_name, index=index_name)
            except Exception as e:
                logger.warning("index_drop_failed", collection=collection_name, error=str(e))
