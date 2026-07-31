"""
Database CLI management commands

Usage:
  python -m app.cli.db migrate
  python -m app.cli.db rollback
  python -m app.cli.db seed <org_id>
  python -m app.cli.db reset <org_id>
"""

import asyncio
import sys
from typing import Optional

import structlog

from app.core.database import connect_db, close_db, db_client
from app.db import run_migrations, rollback_migrations, seed_all, clear_seeds


logger = structlog.get_logger()


async def migrate() -> None:
    """Run all pending migrations"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("Running database migrations...")
        await run_migrations(db)
        logger.info("✅ Migrations completed")

    except Exception as e:
        logger.error("Migration failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def rollback() -> None:
    """Rollback all migrations (DESTRUCTIVE)"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.warning("Rolling back migrations (DESTRUCTIVE)...")
        await rollback_migrations(db)
        logger.info("✅ Rollback completed")

    except Exception as e:
        logger.error("Rollback failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def seed(org_id: str) -> None:
    """Seed initial data for organization"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.info("Seeding database...", org_id=org_id)
        await seed_all(db, org_id)
        logger.info("✅ Seeding completed", org_id=org_id)

    except Exception as e:
        logger.error("Seeding failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def reset(org_id: str) -> None:
    """Reset database for organization"""
    try:
        await connect_db()
        db = db_client[db_client.list_database_names()[0]]

        logger.warning("Resetting database...", org_id=org_id)
        await clear_seeds(db, org_id)
        logger.info("✅ Reset completed", org_id=org_id)

    except Exception as e:
        logger.error("Reset failed", error=str(e))
        sys.exit(1)
    finally:
        await close_db()


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        await migrate()
    elif command == "rollback":
        await rollback()
    elif command == "seed":
        if len(sys.argv) < 3:
            print("Usage: python -m app.cli.db seed <org_id>")
            sys.exit(1)
        await seed(sys.argv[2])
    elif command == "reset":
        if len(sys.argv) < 3:
            print("Usage: python -m app.cli.db reset <org_id>")
            sys.exit(1)
        await reset(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
