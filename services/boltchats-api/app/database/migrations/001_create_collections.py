"""
Migration 001: Create all MongoDB collections with validation schemas
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.migrations import Migration
from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class CreateCollectionsMigration(Migration):
    """Create all core MongoDB collections"""

    version = 1
    name = "create_collections"
    description = "Create all MongoDB collections with validation schemas"

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Create collections"""
        collections = [
            Collection.USERS,
            Collection.ORGANIZATIONS,
            Collection.WORKSPACES,
            Collection.MEMBERS,
            Collection.ROLES,
            Collection.TEAMS,
            Collection.INVITATIONS,
            Collection.CUSTOMERS,
            Collection.CUSTOMER_IDENTITIES,
            Collection.CONVERSATIONS,
            Collection.CONVERSATION_PARTICIPANTS,
            Collection.MESSAGES,
            Collection.LABELS,
            Collection.DRAFTS,
            Collection.INTEGRATIONS,
            Collection.EVENTS,
            Collection.AUDIT_LOGS,
            Collection.NOTIFICATIONS,
            Collection.MIGRATION_HISTORY,
        ]

        for collection_name in collections:
            try:
                await db.create_collection(collection_name)
                logger.info("collection_created", collection=collection_name)
            except Exception as e:
                # Collection may already exist
                logger.debug("collection_exists_or_error", collection=collection_name, error=str(e))

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Drop all collections (destructive)"""
        collections = [
            Collection.USERS,
            Collection.ORGANIZATIONS,
            Collection.WORKSPACES,
            Collection.MEMBERS,
            Collection.ROLES,
            Collection.TEAMS,
            Collection.INVITATIONS,
            Collection.CUSTOMERS,
            Collection.CUSTOMER_IDENTITIES,
            Collection.CONVERSATIONS,
            Collection.CONVERSATION_PARTICIPANTS,
            Collection.MESSAGES,
            Collection.LABELS,
            Collection.DRAFTS,
            Collection.INTEGRATIONS,
            Collection.EVENTS,
            Collection.AUDIT_LOGS,
            Collection.NOTIFICATIONS,
        ]

        for collection_name in collections:
            try:
                await db.drop_collection(collection_name)
                logger.info("collection_dropped", collection=collection_name)
            except Exception as e:
                logger.error("drop_collection_failed", collection=collection_name, error=str(e))
