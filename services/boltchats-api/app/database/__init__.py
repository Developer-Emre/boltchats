"""
Database module — migrations, seeders, validators, health checks

This module handles all database operations:
- Versioned migrations (001_*, 002_*, etc.)
- Seeding with templates
- Schema validation
- Health monitoring
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from .migrations import MigrationManager
from .seeders import SeedManager
from .health import DatabaseHealth


__all__ = [
    "MigrationManager",
    "SeedManager",
    "DatabaseHealth",
    "run_migrations",
    "run_seeders",
]


async def run_migrations(db: AsyncIOMotorDatabase, target_version: int | None = None) -> dict:
    """
    Run all pending migrations.

    Args:
        db: Motor database instance
        target_version: Optional specific version to migrate to

    Returns:
        Migration result dict with count and versions applied
    """
    manager = MigrationManager(db)
    return await manager.migrate(target_version=target_version)


async def run_seeders(
    db: AsyncIOMotorDatabase,
    org_id: str,
    reset: bool = False,
) -> dict:
    """
    Run seeders for organization.

    Args:
        db: Motor database instance
        org_id: Organization ID to seed
        reset: Whether to reset (delete) existing seeded data

    Returns:
        Seeding result dict
    """
    manager = SeedManager(db)
    if reset:
        return await manager.reseed(org_id)
    return await manager.seed(org_id)


async def verify_database(db: AsyncIOMotorDatabase) -> dict:
    """
    Verify database health and integrity.

    Args:
        db: Motor database instance

    Returns:
        Health check result dict
    """
    health = DatabaseHealth(db)
    return await health.check_all()
