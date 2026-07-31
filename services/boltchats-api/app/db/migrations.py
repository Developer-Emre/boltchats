"""
Database migrations and initialization

MongoDB migrations use Mongosh scripts.
This module handles initialization, seeding, and index creation.
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import RoleEnum, PermissionEnum
from app.utils.sparkquark_constants import Collection


class Migration:
    """Migration base class"""

    def __init__(self, name: str, version: int):
        self.name = name
        self.version = version
        self.applied_at: datetime | None = None

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Apply migration"""
        raise NotImplementedError

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Rollback migration"""
        raise NotImplementedError


class CreateCollectionsMigration(Migration):
    """Create all MongoDB collections with initial indexes"""

    def __init__(self):
        super().__init__("create_collections", 1)

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
        ]

        for collection_name in collections:
            try:
                await db.create_collection(collection_name)
            except Exception:
                # Collection may already exist
                pass

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
            except Exception:
                pass


class CreateIndexesMigration(Migration):
    """Create database indexes for performance"""

    def __init__(self):
        super().__init__("create_indexes", 2)

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Create indexes"""
        # Users indexes
        await db[Collection.USERS].create_index("email", unique=True)

        # Organizations indexes
        await db[Collection.ORGANIZATIONS].create_index("slug", unique=True)

        # Members indexes
        await db[Collection.MEMBERS].create_index(
            [("organization_id", 1), ("workspace_id", 1)]
        )
        await db[Collection.MEMBERS].create_index(
            [("organization_id", 1), ("user_id", 1)],
            unique=True,
        )
        await db[Collection.MEMBERS].create_index("email")

        # Customers indexes
        await db[Collection.CUSTOMERS].create_index(
            [("organization_id", 1), ("email", 1)]
        )

        # Customer identities indexes
        await db[Collection.CUSTOMER_IDENTITIES].create_index(
            [("customer_id", 1), ("provider", 1)],
            unique=True,
        )
        await db[Collection.CUSTOMER_IDENTITIES].create_index(
            [("provider", 1), ("external_id", 1)]
        )

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

        # Messages indexes
        await db[Collection.MESSAGES].create_index(
            [("conversation_id", 1), ("created_at", -1)]
        )
        await db[Collection.MESSAGES].create_index("sender_id")
        await db[Collection.MESSAGES].create_index("created_at")

        # Labels indexes
        await db[Collection.LABELS].create_index(
            [("organization_id", 1), ("name", 1)],
            unique=True,
        )

        # Drafts indexes
        await db[Collection.DRAFTS].create_index(
            [("conversation_id", 1), ("member_id", 1)],
            unique=True,
        )

        # Integrations indexes
        await db[Collection.INTEGRATIONS].create_index(
            [("organization_id", 1), ("provider", 1)]
        )

        # Events indexes (event sourcing)
        await db[Collection.EVENTS].create_index(
            [("organization_id", 1), ("created_at", -1)]
        )
        await db[Collection.EVENTS].create_index(
            [("aggregate_id", 1), ("aggregate_type", 1)]
        )
        await db[Collection.EVENTS].create_index("status")

        # Audit logs indexes
        await db[Collection.AUDIT_LOGS].create_index(
            [("organization_id", 1), ("created_at", -1)]
        )
        await db[Collection.AUDIT_LOGS].create_index("resource_id")

        # Notifications indexes
        await db[Collection.NOTIFICATIONS].create_index(
            [("organization_id", 1), ("recipient_id", 1), ("created_at", -1)]
        )
        await db[Collection.NOTIFICATIONS].create_index("status")

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
        ]

        for collection_name in collections:
            try:
                await db[collection_name].drop_indexes()
            except Exception:
                pass


async def run_migrations(db: AsyncIOMotorDatabase) -> None:
    """Run all pending migrations"""
    migrations = [
        CreateCollectionsMigration(),
        CreateIndexesMigration(),
    ]

    for migration in migrations:
        await migration.up(db)


async def rollback_migrations(db: AsyncIOMotorDatabase) -> None:
    """Rollback all migrations (destructive)"""
    migrations = [
        CreateIndexesMigration(),
        CreateCollectionsMigration(),
    ]

    for migration in reversed(migrations):
        await migration.down(db)
