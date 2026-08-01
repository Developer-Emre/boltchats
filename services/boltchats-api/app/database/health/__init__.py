"""
Database health and integrity monitoring

Checks:
- MongoDB connection
- Redis connection (if applicable)
- Collections existence
- Indexes status
- Migrations consistency
- TTL configuration
"""

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from app.utils.sparkquark_constants import Collection

import structlog

logger = structlog.get_logger(__name__)


class DatabaseHealth:
    """Database health monitoring"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def check_all(self) -> dict:
        """
        Run all health checks.

        Returns:
            Health check result dict
        """
        logger.info("health_check_start")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ok",
            "checks": {},
            "errors": [],
        }

        # MongoDB connection
        try:
            conn_check = await self._check_connection()
            result["checks"]["mongodb"] = conn_check
        except Exception as e:
            logger.error("mongodb_check_failed", error=str(e))
            result["errors"].append(f"MongoDB: {str(e)}")
            result["status"] = "error"

        # Collections
        try:
            collections_check = await self._check_collections()
            result["checks"]["collections"] = collections_check
        except Exception as e:
            logger.error("collections_check_failed", error=str(e))
            result["errors"].append(f"Collections: {str(e)}")

        # Indexes
        try:
            indexes_check = await self._check_indexes()
            result["checks"]["indexes"] = indexes_check
        except Exception as e:
            logger.error("indexes_check_failed", error=str(e))
            result["errors"].append(f"Indexes: {str(e)}")

        # Migrations
        try:
            migrations_check = await self._check_migrations()
            result["checks"]["migrations"] = migrations_check
        except Exception as e:
            logger.error("migrations_check_failed", error=str(e))
            result["errors"].append(f"Migrations: {str(e)}")

        # TTL configuration
        try:
            ttl_check = await self._check_ttl()
            result["checks"]["ttl"] = ttl_check
        except Exception as e:
            logger.error("ttl_check_failed", error=str(e))
            result["errors"].append(f"TTL: {str(e)}")

        logger.info("health_check_complete", status=result["status"])
        return result

    async def _check_connection(self) -> dict:
        """Check MongoDB connection"""
        try:
            await self.db.client.server_info()
            return {"status": "ok", "message": "Connected to MongoDB"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _check_collections(self) -> dict:
        """Check if all required collections exist"""
        required_collections = [
            Collection.USERS,
            Collection.ORGANIZATIONS,
            Collection.MEMBERS,
            Collection.CONVERSATIONS,
            Collection.MESSAGES,
            Collection.CUSTOMERS,
            Collection.EVENTS,
            Collection.AUDIT_LOGS,
            Collection.NOTIFICATIONS,
        ]

        existing_collections = await self.db.list_collection_names()

        missing = [c for c in required_collections if c not in existing_collections]
        present = [c for c in required_collections if c in existing_collections]

        return {
            "status": "ok" if not missing else "warning",
            "total_required": len(required_collections),
            "present": len(present),
            "missing": missing,
        }

    async def _check_indexes(self) -> dict:
        """Check indexes status"""
        index_summary = {}
        total_indexes = 0

        critical_collections = [
            Collection.USERS,
            Collection.ORGANIZATIONS,
            Collection.MEMBERS,
            Collection.CONVERSATIONS,
            Collection.MESSAGES,
        ]

        for collection_name in critical_collections:
            try:
                indexes = await self.db[collection_name].list_indexes().to_list(None)
                index_count = len(indexes)
                total_indexes += index_count
                index_summary[collection_name] = {
                    "count": index_count,
                    "indexes": [idx["name"] for idx in indexes],
                }
            except Exception as e:
                index_summary[collection_name] = {"error": str(e)}

        return {
            "status": "ok",
            "total_indexes": total_indexes,
            "collections": index_summary,
        }

    async def _check_migrations(self) -> dict:
        """Check migrations status"""
        try:
            history = await self.db[Collection.MIGRATION_HISTORY].find().to_list(None)
            return {
                "status": "ok",
                "total_applied": len(history),
                "latest_version": max([m["version"] for m in history]) if history else 0,
                "applied_versions": sorted([m["version"] for m in history]),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    async def _check_ttl(self) -> dict:
        """Check TTL indexes status"""
        ttl_collections = [
            Collection.DRAFTS,
            Collection.NOTIFICATIONS,
        ]

        ttl_status = {}

        for collection_name in ttl_collections:
            try:
                indexes = await self.db[collection_name].list_indexes().to_list(None)
                ttl_indexes = [
                    {
                        "name": idx["name"],
                        "expireAfterSeconds": idx.get("expireAfterSeconds", "N/A"),
                    }
                    for idx in indexes
                    if "expireAfterSeconds" in idx
                ]
                ttl_status[collection_name] = {
                    "has_ttl": len(ttl_indexes) > 0,
                    "ttl_indexes": ttl_indexes,
                }
            except Exception as e:
                ttl_status[collection_name] = {"error": str(e)}

        return {
            "status": "ok",
            "collections": ttl_status,
        }
