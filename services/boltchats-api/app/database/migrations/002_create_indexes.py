"""
Migration 002: Create database indexes for performance
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.migrations import Migration
from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class CreateIndexesMigration(Migration):
    """Create performance indexes for all collections"""

    version = 2
    name = "create_indexes"
    description = "Create database indexes for query performance"

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Create indexes"""
        # Users indexes
        await db[Collection.USERS].create_index("email", unique=True)
        logger.info("index_created", collection=Collection.USERS, fields="email")

        # Organizations indexes
        await db[Collection.ORGANIZATIONS].create_index("slug", unique=True)
        logger.info("index_created", collection=Collection.ORGANIZATIONS, fields="slug")

        # Members indexes
        await db[Collection.MEMBERS].create_index([("organization_id", 1), ("workspace_id", 1)])
        await db[Collection.MEMBERS].create_index(
            [("organization_id", 1), ("user_id", 1)],
            unique=True,
        )
        await db[Collection.MEMBERS].create_index("email")
        logger.info("index_created", collection=Collection.MEMBERS, fields="multi")

        # Customers indexes
        await db[Collection.CUSTOMERS].create_index([("organization_id", 1), ("email", 1)])
        logger.info("index_created", collection=Collection.CUSTOMERS, fields="org+email")

        # Customer identities indexes
        await db[Collection.CUSTOMER_IDENTITIES].create_index(
            [("customer_id", 1), ("provider", 1)],
            unique=True,
        )
        await db[Collection.CUSTOMER_IDENTITIES].create_index(
            [("provider", 1), ("external_id", 1)]
        )
        logger.info("index_created", collection=Collection.CUSTOMER_IDENTITIES, fields="multi")

        # Conversations indexes
        await db[Collection.CONVERSATIONS].create_index(
            [("organization_id", 1), ("customer_id", 1), ("channel", 1)]
        )
        await db[Collection.CONVERSATIONS].create_index(
            [("organization_id", 1), ("status", 1)]
        )
        await db[Collection.CONVERSATIONS].create_index(
            [("organization_id", 1), ("assigned_to", 1)]
        )
        await db[Collection.CONVERSATIONS].create_index("created_at")
        logger.info("index_created", collection=Collection.CONVERSATIONS, fields="multi")

        # Messages indexes
        await db[Collection.MESSAGES].create_index(
            [("conversation_id", 1), ("created_at", -1)]
        )
        await db[Collection.MESSAGES].create_index("sender_id")
        await db[Collection.MESSAGES].create_index("created_at")
        logger.info("index_created", collection=Collection.MESSAGES, fields="multi")

        # Labels indexes
        await db[Collection.LABELS].create_index(
            [("organization_id", 1), ("name", 1)],
            unique=True,
        )
        logger.info("index_created", collection=Collection.LABELS, fields="org+name")

        # Drafts indexes
        await db[Collection.DRAFTS].create_index(
            [("conversation_id", 1), ("member_id", 1)],
            unique=True,
        )
        logger.info("index_created", collection=Collection.DRAFTS, fields="conv+member")

        # Integrations indexes
        await db[Collection.INTEGRATIONS].create_index(
            [("organization_id", 1), ("provider", 1)]
        )
        logger.info("index_created", collection=Collection.INTEGRATIONS, fields="org+provider")

        # Events indexes (event sourcing)
        await db[Collection.EVENTS].create_index(
            [("organization_id", 1), ("created_at", -1)]
        )
        await db[Collection.EVENTS].create_index(
            [("aggregate_id", 1), ("aggregate_type", 1)]
        )
        await db[Collection.EVENTS].create_index("status")
        logger.info("index_created", collection=Collection.EVENTS, fields="multi")

        # Audit logs indexes
        await db[Collection.AUDIT_LOGS].create_index(
            [("organization_id", 1), ("created_at", -1)]
        )
        await db[Collection.AUDIT_LOGS].create_index("resource_id")
        logger.info("index_created", collection=Collection.AUDIT_LOGS, fields="multi")

        # Notifications indexes
        await db[Collection.NOTIFICATIONS].create_index(
            [("organization_id", 1), ("recipient_id", 1), ("created_at", -1)]
        )
        await db[Collection.NOTIFICATIONS].create_index("status")
        logger.info("index_created", collection=Collection.NOTIFICATIONS, fields="multi")

        # Teams indexes
        await db[Collection.TEAMS].create_index(
            [("organization_id", 1), ("workspace_id", 1)]
        )
        logger.info("index_created", collection=Collection.TEAMS, fields="org+ws")

        # Conversation participants indexes
        await db[Collection.CONVERSATION_PARTICIPANTS].create_index(
            [("conversation_id", 1), ("member_id", 1)],
            unique=True,
        )
        await db[Collection.CONVERSATION_PARTICIPANTS].create_index(
            [("organization_id", 1), ("member_id", 1)]
        )
        logger.info("index_created", collection=Collection.CONVERSATION_PARTICIPANTS, fields="multi")

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Drop all indexes"""
        collections = [
            Collection.USERS,
            Collection.ORGANIZATIONS,
            Collection.MEMBERS,
            Collection.CUSTOMERS,
            Collection.CUSTOMER_IDENTITIES,
            Collection.CONVERSATIONS,
            Collection.MESSAGES,
            Collection.LABELS,
            Collection.DRAFTS,
            Collection.INTEGRATIONS,
            Collection.EVENTS,
            Collection.AUDIT_LOGS,
            Collection.NOTIFICATIONS,
            Collection.TEAMS,
            Collection.CONVERSATION_PARTICIPANTS,
        ]

        for collection_name in collections:
            try:
                await db[collection_name].drop_indexes()
                logger.info("indexes_dropped", collection=collection_name)
            except Exception as e:
                logger.error("drop_indexes_failed", collection=collection_name, error=str(e))
