"""
Database backup and restore utilities

Production recommendations:
- Local: Use mongodump/mongorestore
- Production Atlas: Use Atlas Backup service
- Automation: Use scheduled jobs
"""

import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class BackupManager:
    """Database backup and restore management"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    async def backup_database(
        self,
        mongo_uri: str,
        database_name: str,
        tags: list[str] | None = None,
    ) -> dict:
        """
        Create a database backup using mongodump.

        Args:
            mongo_uri: MongoDB connection URI
            database_name: Database name to backup
            tags: Optional tags to add to backup

        Returns:
            Backup result dict
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{database_name}_{timestamp}"
        backup_path = self.backup_dir / backup_name

        logger.info("backup_start", database=database_name, path=str(backup_path))

        try:
            cmd = [
                "mongodump",
                "--uri", mongo_uri,
                "--db", database_name,
                "--out", str(backup_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"mongodump failed: {error_msg}")

            logger.info("backup_complete", database=database_name, path=str(backup_path))

            return {
                "status": "success",
                "database": database_name,
                "path": str(backup_path),
                "timestamp": timestamp,
                "tags": tags or [],
            }

        except Exception as e:
            logger.error("backup_failed", database=database_name, error=str(e))
            return {
                "status": "error",
                "database": database_name,
                "error": str(e),
            }

    async def restore_database(
        self,
        mongo_uri: str,
        backup_path: str,
        drop: bool = False,
    ) -> dict:
        """
        Restore a database from backup using mongorestore.

        Args:
            mongo_uri: MongoDB connection URI
            backup_path: Path to backup directory
            drop: Whether to drop existing database before restore

        Returns:
            Restore result dict
        """
        logger.warning("restore_start", path=backup_path, drop=drop)

        try:
            cmd = [
                "mongorestore",
                "--uri", mongo_uri,
                str(backup_path),
            ]

            if drop:
                cmd.insert(2, "--drop")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"mongorestore failed: {error_msg}")

            logger.info("restore_complete", path=backup_path)

            return {
                "status": "success",
                "path": backup_path,
                "drop": drop,
            }

        except Exception as e:
            logger.error("restore_failed", path=backup_path, error=str(e))
            return {
                "status": "error",
                "path": backup_path,
                "error": str(e),
            }

    def list_backups(self) -> list[dict]:
        """List all available backups"""
        backups = []

        for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_dir.is_dir():
                stat = backup_dir.stat()
                backups.append({
                    "name": backup_dir.name,
                    "path": str(backup_dir),
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "size_bytes": sum(
                        f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()
                    ),
                })

        return backups
