"""
Migration 003: Add TTL (Time To Live) indexes for automatic cleanup
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.migrations import Migration
from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class AddTTLIndexesMigration(Migration):
    """Add TTL indexes for automatic document expiration"""

    version = 3
    name = "add_ttl_indexes"
    description = "Add TTL indexes for automatic cleanup of temporary data"

    # TTL durations in seconds
    TTL_DRAFT = 7 * 24 * 60 * 60  # 7 days
    TTL_NOTIFICATION = 30 * 24 * 60 * 60  # 30 days
    TTL_WEBHOOK_DELIVERY = 90 * 24 * 60 * 60  # 90 days
    TTL_REFRESH_TOKEN = 7 * 24 * 60 * 60  # 7 days
    TTL_EVENT_RETRY = 24 * 60 * 60  # 1 day

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Create TTL indexes"""
        # Drafts: expire after 7 days
        await db[Collection.DRAFTS].create_index(
            "created_at",
            expireAfterSeconds=self.TTL_DRAFT,
        )
        logger.info("ttl_index_created", collection=Collection.DRAFTS, ttl_days=7)

        # Notifications: expire after 30 days
        await db[Collection.NOTIFICATIONS].create_index(
            "created_at",
            expireAfterSeconds=self.TTL_NOTIFICATION,
        )
        logger.info("ttl_index_created", collection=Collection.NOTIFICATIONS, ttl_days=30)

        # Events retry: expire after 1 day
        # (assuming event_type field exists or create a separate collection)
        try:
            await db[Collection.EVENTS].create_index(
                "created_at",
                expireAfterSeconds=self.TTL_EVENT_RETRY,
                partialFilterExpression={"status": "retry_pending"},
            )
            logger.info("ttl_index_created", collection=Collection.EVENTS, ttl_days=1)
        except Exception as e:
            logger.warning("ttl_index_partial_failed", collection=Collection.EVENTS, error=str(e))

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Remove TTL indexes"""
        collections_with_ttl = [
            Collection.DRAFTS,
            Collection.NOTIFICATIONS,
            Collection.EVENTS,
        ]

        for collection_name in collections_with_ttl:
            try:
                # Drop specific TTL indexes
                indexes = await db[collection_name].list_indexes().to_list(None)
                for index in indexes:
                    if index.get("expireAfterSeconds"):
                        await db[collection_name].drop_index(index["name"])
                        logger.info("ttl_index_dropped", collection=collection_name, index=index["name"])
            except Exception as e:
                logger.error("drop_ttl_index_failed", collection=collection_name, error=str(e))
