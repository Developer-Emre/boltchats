"""
Database CLI management commands (Production-Ready)

Usage:
  python -m app.cli.db migrate [--version N]
  python -m app.cli.db rollback [--steps N]
  python -m app.cli.db seed <org_id>
  python -m app.cli.db reseed <org_id>
  python -m app.cli.db status
  python -m app.cli.db verify
  python -m app.cli.db health
  python -m app.cli.db repair
"""

import asyncio
import sys
import json
from typing import Optional

import structlog

from app.core.database import connect_db, close_db, db_client
from app.database import MigrationManager, SeedManager, DatabaseHealth
from app.database.validators import DatabaseValidator


logger = structlog.get_logger()


async def migrate(target_version: Optional[int] = None) -> None:
    """Run pending migrations"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("🔄 Running migrations...", target_version=target_version)
        manager = MigrationManager(db)
        result = await manager.migrate(target_version=target_version)

        if result["status"] == "success":
            logger.info("✅ Migrations completed", applied=len(result["applied"]))
            print(json.dumps(result, indent=2, default=str))
        else:
            logger.error("❌ Migration had errors", failed=len(result["failed"]))
            print(json.dumps(result, indent=2, default=str))
            sys.exit(1)

    except Exception as e:
        logger.error("❌ Migration failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def rollback(steps: int = 1) -> None:
    """Rollback migrations"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.warning("⏮️  Rolling back migrations...", steps=steps)
        manager = MigrationManager(db)
        result = await manager.rollback(steps=steps)

        if result["status"] == "success":
            logger.info("✅ Rollback completed", rolled_back=len(result["rolled_back"]))
            print(json.dumps(result, indent=2, default=str))
        else:
            logger.error("❌ Rollback had errors", failed=len(result["failed"]))
            print(json.dumps(result, indent=2, default=str))
            sys.exit(1)

    except Exception as e:
        logger.error("❌ Rollback failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def seed(org_id: str) -> None:
    """Seed organization with template roles"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("🌱 Seeding organization...", org_id=org_id)
        manager = SeedManager(db)
        result = await manager.seed(org_id)

        logger.info("✅ Seeding completed", org_id=org_id, roles=result["roles_created"])
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Seeding failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def reseed(org_id: str) -> None:
    """Reseed organization (delete and recreate)"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.warning("🔄 Reseeding organization...", org_id=org_id)
        manager = SeedManager(db)
        result = await manager.reseed(org_id)

        logger.info("✅ Reseed completed", org_id=org_id)
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Reseed failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def status() -> None:
    """Show migration status"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        manager = MigrationManager(db)
        verification = await manager.verify()

        logger.info("📊 Migration Status")
        print(json.dumps(verification, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Status check failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def verify() -> None:
    """Verify migrations consistency"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("🔍 Verifying migrations...")
        manager = MigrationManager(db)
        result = await manager.verify()

        if result["status"] == "ok":
            logger.info("✅ Migrations verified")
        else:
            logger.warning("⚠️  Issues found", missing=result["missing"], orphaned=result["orphaned"])

        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Verification failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def health() -> None:
    """Check database health"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("🏥 Checking database health...")
        health_check = DatabaseHealth(db)
        result = await health_check.check_all()

        if result["status"] == "ok":
            logger.info("✅ Database healthy")
        else:
            logger.warning("⚠️  Issues detected", error_count=len(result["errors"]))

        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Health check failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def repair() -> None:
    """Repair database issues"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.warning("🔧 Attempting database repairs...")
        validator = DatabaseValidator(db)
        result = await validator.repair_all()

        logger.info("✅ Repair completed")
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Repair failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def validate() -> None:
    """Validate database integrity"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("🔍 Validating database...")
        validator = DatabaseValidator(db)
        result = await validator.validate_all()

        if result["status"] == "ok":
            logger.info("✅ Database valid")
        else:
            logger.warning("⚠️  Issues found", issue_count=len(result["issues"]))

        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error("❌ Validation failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


def print_help():
    """Print help message"""
    print(__doc__)


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1]

    if command == "migrate":
        version = None
        if len(sys.argv) > 3 and sys.argv[2] == "--version":
            try:
                version = int(sys.argv[3])
            except ValueError:
                logger.error("Invalid version number")
                sys.exit(1)
        await migrate(target_version=version)

    elif command == "rollback":
        steps = 1
        if len(sys.argv) > 3 and sys.argv[2] == "--steps":
            try:
                steps = int(sys.argv[3])
            except ValueError:
                logger.error("Invalid steps number")
                sys.exit(1)
        await rollback(steps=steps)

    elif command == "seed":
        if len(sys.argv) < 3:
            logger.error("Usage: python -m app.cli.db seed <org_id>")
            sys.exit(1)
        await seed(sys.argv[2])

    elif command == "reseed":
        if len(sys.argv) < 3:
            logger.error("Usage: python -m app.cli.db reseed <org_id>")
            sys.exit(1)
        await reseed(sys.argv[2])

    elif command == "status":
        await status()

    elif command == "verify":
        await verify()

    elif command == "health":
        await health()

    elif command == "repair":
        await repair()

    elif command == "validate":
        await validate()

    elif command == "help":
        print_help()

    else:
        logger.error("Unknown command", command=command)
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
