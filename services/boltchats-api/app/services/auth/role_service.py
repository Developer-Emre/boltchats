"""
Role Service

Seed and manage default roles for organizations
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.identity import PermissionEnum, RoleDocument
from app.repositories import RoleRepository


class RoleService:
    """Handle role creation and default role seeding"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.roles = RoleRepository(db)

    async def seed_default_roles(self, organization_id: str) -> dict[str, str]:
        """
        Seed default roles for a new organization.
        
        Follows Register_flow.md Step 5.
        
        Roles created:
        - Admin: Full access (conversation:*, member:*, team:*, integration:*)
        - Manager: Team management (team:*, conversation:read, conversation:write)
        - Agent: Handle conversations (conversation:read, conversation:write, message:*)
        - Viewer: Read-only access (conversation:read, message:read, customer:read)
        
        Args:
            organization_id: Organization ID
            
        Returns:
            {
                "admin_role_id": "...",
                "manager_role_id": "...",
                "agent_role_id": "...",
                "viewer_role_id": "..."
            }
        """
        # Define default roles with their permissions
        default_roles = [
            {
                "name": "admin",
                "permissions": [
                    PermissionEnum.ORG_READ.value,
                    PermissionEnum.ORG_WRITE.value,
                    PermissionEnum.ORG_DELETE.value,
                    PermissionEnum.MEMBER_READ.value,
                    PermissionEnum.MEMBER_WRITE.value,
                    PermissionEnum.MEMBER_DELETE.value,
                    PermissionEnum.TEAM_READ.value,
                    PermissionEnum.TEAM_WRITE.value,
                    PermissionEnum.TEAM_DELETE.value,
                    PermissionEnum.CONVERSATION_READ.value,
                    PermissionEnum.CONVERSATION_WRITE.value,
                    PermissionEnum.CONVERSATION_DELETE.value,
                    PermissionEnum.MESSAGE_READ.value,
                    PermissionEnum.MESSAGE_WRITE.value,
                    PermissionEnum.MESSAGE_DELETE.value,
                    PermissionEnum.INTERNAL_NOTE_READ.value,
                    PermissionEnum.INTERNAL_NOTE_WRITE.value,
                    PermissionEnum.INTERNAL_NOTE_DELETE.value,
                    PermissionEnum.LABEL_READ.value,
                    PermissionEnum.LABEL_WRITE.value,
                    PermissionEnum.LABEL_DELETE.value,
                    PermissionEnum.ASSIGNMENT_READ.value,
                    PermissionEnum.ASSIGNMENT_WRITE.value,
                    PermissionEnum.ASSIGNMENT_DELETE.value,
                    PermissionEnum.CUSTOMER_READ.value,
                    PermissionEnum.CUSTOMER_WRITE.value,
                    PermissionEnum.CUSTOMER_DELETE.value,
                    PermissionEnum.INTEGRATION_READ.value,
                    PermissionEnum.INTEGRATION_WRITE.value,
                    PermissionEnum.INTEGRATION_DELETE.value,
                    PermissionEnum.ANALYTICS_READ.value,
                    PermissionEnum.AUDIT_LOG_READ.value,
                ]
            },
            {
                "name": "manager",
                "permissions": [
                    PermissionEnum.TEAM_READ.value,
                    PermissionEnum.TEAM_WRITE.value,
                    PermissionEnum.MEMBER_READ.value,
                    PermissionEnum.CONVERSATION_READ.value,
                    PermissionEnum.CONVERSATION_WRITE.value,
                    PermissionEnum.MESSAGE_READ.value,
                    PermissionEnum.MESSAGE_WRITE.value,
                    PermissionEnum.CUSTOMER_READ.value,
                    PermissionEnum.ANALYTICS_READ.value,
                    PermissionEnum.AUDIT_LOG_READ.value,
                ]
            },
            {
                "name": "agent",
                "permissions": [
                    PermissionEnum.CONVERSATION_READ.value,
                    PermissionEnum.CONVERSATION_WRITE.value,
                    PermissionEnum.MESSAGE_READ.value,
                    PermissionEnum.MESSAGE_WRITE.value,
                    PermissionEnum.INTERNAL_NOTE_READ.value,
                    PermissionEnum.INTERNAL_NOTE_WRITE.value,
                    PermissionEnum.CUSTOMER_READ.value,
                    PermissionEnum.LABEL_READ.value,
                ]
            },
            {
                "name": "viewer",
                "permissions": [
                    PermissionEnum.CONVERSATION_READ.value,
                    PermissionEnum.MESSAGE_READ.value,
                    PermissionEnum.CUSTOMER_READ.value,
                    PermissionEnum.ANALYTICS_READ.value,
                ]
            },
        ]

        role_ids = {}

        for role_config in default_roles:
            role = RoleDocument(
                organization_id=organization_id,
                name=role_config["name"],
                permissions=role_config["permissions"],
            )
            role_id = await self.roles.create(role)
            role_ids[f"{role_config['name']}_role_id"] = role_id

        return role_ids
