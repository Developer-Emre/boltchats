"""
Database migration system with versioning and history tracking.

Features:
- Numbered migration files (001_*, 002_*, etc.)
- Migration history tracking in MongoDB
- Automatic rollback detection
- Safe production migrations
"""

import os
import importlib.util
from datetime import datetime, timezone
from typing import Type

from motor.motor_asyncio import AsyncIOMotorDatabase

import structlog

logger = structlog.get_logger(__name__)


class Migration:
    """Base migration class"""

    version: int
    name: str
    description: str = ""

    async def up(self, db: AsyncIOMotorDatabase) -> None:
        """Apply migration"""
        raise NotImplementedError

    async def down(self, db: AsyncIOMotorDatabase) -> None:
        """Rollback migration"""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Migration(v{self.version}, {self.name})"


class MigrationManager:
    """Manages database migrations with version history"""

    MIGRATION_DIR = os.path.join(os.path.dirname(__file__))
    HISTORY_COLLECTION = "migration_history"

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._migrations: dict[int, Migration] = {}

    async def _ensure_history_collection(self) -> None:
        """Ensure migration_history collection exists"""
        try:
            await self.db[self.HISTORY_COLLECTION].create_index("version", unique=True)
        except Exception:
            # Collection already exists
            pass

    async def _load_migrations(self) -> dict[int, Migration]:
        """Load all migration classes from migration files"""
        if self._migrations:
            return self._migrations

        migrations = {}

        # List all migration files (001_*.py, 002_*.py, etc.)
        files = sorted([
            f for f in os.listdir(self.MIGRATION_DIR)
            if f.startswith(tuple("0123456789")) and f.endswith(".py") and f != "__init__.py"
        ])

        for filename in files:
            try:
                filepath = os.path.join(self.MIGRATION_DIR, filename)
                spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find Migration subclass in module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, Migration) and
                            attr is not Migration):
                            migration = attr()
                            migrations[migration.version] = migration
                            logger.info("loaded_migration", version=migration.version, name=migration.name)

            except Exception as e:
                logger.error("failed_loading_migration", filename=filename, error=str(e))

        self._migrations = migrations
        return migrations

    async def get_current_version(self) -> int:
        """Get current applied migration version"""
        await self._ensure_history_collection()

        history = await self.db[self.HISTORY_COLLECTION].find_one(
            {},
            sort=[("version", -1)]
        )

        return history["version"] if history else 0

    async def get_applied_migrations(self) -> list[dict]:
        """Get list of applied migrations"""
        await self._ensure_history_collection()

        return await self.db[self.HISTORY_COLLECTION].find().to_list(None)

    async def migrate(self, target_version: int | None = None) -> dict:
        """
        Run pending migrations.

        Args:
            target_version: Optional specific version to migrate to

        Returns:
            Migration result dict
        """
        await self._ensure_history_collection()
        migrations = await self._load_migrations()

        current_version = await self.get_current_version()
        logger.info("migrate_start", current_version=current_version, target_version=target_version)

        if not migrations:
            logger.warning("no_migrations_found")
            return {"status": "no_migrations", "current_version": current_version}

        applied = []
        failed = []

        # Sort migrations by version
        sorted_versions = sorted(migrations.keys())

        for version in sorted_versions:
            # Skip if already applied
            if version <= current_version:
                continue

            # Skip if target version specified and not reached yet
            if target_version and version > target_version:
                continue

            migration = migrations[version]

            try:
                logger.info("applying_migration", version=version, name=migration.name)
                await migration.up(self.db)

                # Record in history
                await self.db[self.HISTORY_COLLECTION].insert_one({
                    "version": version,
                    "name": migration.name,
                    "description": migration.description,
                    "applied_at": datetime.now(timezone.utc),
                    "status": "applied",
                })

                applied.append(version)
                logger.info("migration_applied", version=version, name=migration.name)

            except Exception as e:
                logger.error("migration_failed", version=version, name=migration.name, error=str(e))
                failed.append({"version": version, "error": str(e)})

        return {
            "status": "success" if not failed else "partial",
            "applied": applied,
            "failed": failed,
            "current_version": await self.get_current_version(),
            "total_applied": len(applied),
        }

    async def rollback(self, steps: int = 1) -> dict:
        """
        Rollback migrations.

        Args:
            steps: Number of versions to rollback

        Returns:
            Rollback result dict
        """
        await self._ensure_history_collection()
        migrations = await self._load_migrations()

        history = await self.db[self.HISTORY_COLLECTION].find(
            {},
            sort=[("version", -1)]
        ).to_list(steps)

        rolled_back = []
        failed = []

        for record in history:
            version = record["version"]
            if version not in migrations:
                logger.error("migration_not_found", version=version)
                failed.append({"version": version, "error": "Migration not found"})
                continue

            migration = migrations[version]

            try:
                logger.info("rolling_back_migration", version=version, name=migration.name)
                await migration.down(self.db)

                # Remove from history
                await self.db[self.HISTORY_COLLECTION].delete_one({"version": version})

                rolled_back.append(version)
                logger.info("migration_rolled_back", version=version)

            except Exception as e:
                logger.error("rollback_failed", version=version, error=str(e))
                failed.append({"version": version, "error": str(e)})

        return {
            "status": "success" if not failed else "partial",
            "rolled_back": rolled_back,
            "failed": failed,
            "current_version": await self.get_current_version(),
        }

    async def verify(self) -> dict:
        """
        Verify migration consistency.

        Returns:
            Verification result dict
        """
        migrations = await self._load_migrations()
        applied = await self.get_applied_migrations()

        applied_versions = {m["version"] for m in applied}
        expected_versions = set(migrations.keys())

        missing = expected_versions - applied_versions
        orphaned = applied_versions - expected_versions

        return {
            "status": "ok" if not (missing or orphaned) else "issues",
            "total_migrations": len(migrations),
            "applied": len(applied),
            "missing": sorted(missing),
            "orphaned": sorted(orphaned),
            "details": applied,
        }
