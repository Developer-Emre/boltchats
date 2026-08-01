"""
Database seeding system with template roles and initial data

Features:
- Seeding with role templates (Admin, Manager, Agent, Viewer)
- Organization-specific customization
- Reseed capability for clean state
"""

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import RoleEnum, PermissionEnum
from app.utils.sparkquark_constants import Collection
from app.utils.ulid import new_role_id

import structlog

logger = structlog.get_logger(__name__)


class SeedManager:
    """Manages database seeding"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def seed(self, org_id: str) -> dict:
        """
        Seed organization with template roles and initial data.

        Args:
            org_id: Organization ID to seed

        Returns:
            Seeding result dict
        """
        logger.info("seed_start", org_id=org_id)

        result = {
            "organization_id": org_id,
            "roles_created": 0,
            "errors": [],
        }

        try:
            # Seed template roles
            roles_created = await self._seed_roles(org_id)
            result["roles_created"] = roles_created
            logger.info("roles_seeded", org_id=org_id, count=roles_created)

        except Exception as e:
            logger.error("seed_failed", org_id=org_id, error=str(e))
            result["errors"].append(str(e))

        return result

    async def reseed(self, org_id: str) -> dict:
        """
        Reseed organization (delete existing data first).

        Args:
            org_id: Organization ID to reseed

        Returns:
            Reseed result dict
        """
        logger.info("reseed_start", org_id=org_id)

        result = {
            "organization_id": org_id,
            "deleted": {},
            "created": {},
            "errors": [],
        }

        try:
            # Delete existing roles
            delete_result = await self.db[Collection.ROLES].delete_many(
                {"organization_id": org_id}
            )
            result["deleted"]["roles"] = delete_result.deleted_count
            logger.info("roles_deleted", org_id=org_id, count=delete_result.deleted_count)

            # Reseed roles
            roles_created = await self._seed_roles(org_id)
            result["created"]["roles"] = roles_created

        except Exception as e:
            logger.error("reseed_failed", org_id=org_id, error=str(e))
            result["errors"].append(str(e))

        return result

    async def _seed_roles(self, org_id: str) -> int:
        """
        Seed template roles for organization.

        Args:
            org_id: Organization ID

        Returns:
            Number of roles created
        """
        role_templates = [
            {
                "name": "Admin",
                "description": "Full access to all features and settings",
                "permissions": self._get_admin_permissions(),
                "is_template": True,
            },
            {
                "name": "Manager",
                "description": "Manage team members and conversations",
                "permissions": self._get_manager_permissions(),
                "is_template": True,
            },
            {
                "name": "Agent",
                "description": "Handle customer conversations",
                "permissions": self._get_agent_permissions(),
                "is_template": True,
            },
            {
                "name": "Viewer",
                "description": "Read-only access to conversations and reports",
                "permissions": self._get_viewer_permissions(),
                "is_template": True,
            },
        ]

        created = 0

        for template in role_templates:
            try:
                # Check if role already exists
                existing = await self.db[Collection.ROLES].find_one({
                    "organization_id": org_id,
                    "name": template["name"],
                })

                if existing:
                    logger.debug("role_exists", org_id=org_id, name=template["name"])
                    continue

                role_doc = {
                    "_id": new_role_id(),
                    "organization_id": org_id,
                    "name": template["name"],
                    "description": template["description"],
                    "permissions": template["permissions"],
                    "is_template": template["is_template"],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }

                await self.db[Collection.ROLES].insert_one(role_doc)
                created += 1
                logger.debug("role_created", org_id=org_id, role=template["name"])

            except Exception as e:
                logger.error("role_creation_failed", org_id=org_id, role=template["name"], error=str(e))

        return created

    @staticmethod
    def _get_admin_permissions() -> list[str]:
        """Get admin role permissions"""
        return [
            PermissionEnum.ORGANIZATION_MANAGE,
            PermissionEnum.WORKSPACE_MANAGE,
            PermissionEnum.TEAM_MANAGE,
            PermissionEnum.MEMBER_INVITE,
            PermissionEnum.MEMBER_REMOVE,
            PermissionEnum.ROLE_MANAGE,
            PermissionEnum.CONVERSATION_READ,
            PermissionEnum.CONVERSATION_WRITE,
            PermissionEnum.CONVERSATION_ASSIGN,
            PermissionEnum.CONVERSATION_CLOSE,
            PermissionEnum.MESSAGE_SEND,
            PermissionEnum.MESSAGE_EDIT,
            PermissionEnum.MESSAGE_DELETE,
            PermissionEnum.CUSTOMER_MANAGE,
            PermissionEnum.INTEGRATION_MANAGE,
            PermissionEnum.LABEL_MANAGE,
            PermissionEnum.REPORT_VIEW,
            PermissionEnum.AUDIT_LOG_VIEW,
        ]

    @staticmethod
    def _get_manager_permissions() -> list[str]:
        """Get manager role permissions"""
        return [
            PermissionEnum.TEAM_MANAGE,
            PermissionEnum.MEMBER_INVITE,
            PermissionEnum.CONVERSATION_READ,
            PermissionEnum.CONVERSATION_WRITE,
            PermissionEnum.CONVERSATION_ASSIGN,
            PermissionEnum.CONVERSATION_CLOSE,
            PermissionEnum.MESSAGE_SEND,
            PermissionEnum.MESSAGE_EDIT,
            PermissionEnum.CUSTOMER_MANAGE,
            PermissionEnum.LABEL_MANAGE,
            PermissionEnum.REPORT_VIEW,
        ]

    @staticmethod
    def _get_agent_permissions() -> list[str]:
        """Get agent role permissions"""
        return [
            PermissionEnum.CONVERSATION_READ,
            PermissionEnum.CONVERSATION_WRITE,
            PermissionEnum.MESSAGE_SEND,
            PermissionEnum.MESSAGE_EDIT,
            PermissionEnum.MESSAGE_DELETE,
            PermissionEnum.CUSTOMER_VIEW,
        ]

    @staticmethod
    def _get_viewer_permissions() -> list[str]:
        """Get viewer role permissions"""
        return [
            PermissionEnum.CONVERSATION_READ,
            PermissionEnum.CUSTOMER_VIEW,
            PermissionEnum.REPORT_VIEW,
        ]
