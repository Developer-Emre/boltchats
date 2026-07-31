"""
Database seeding

Populates initial data like system roles and permissions
"""

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.models.identity import RoleDocument, PermissionEnum, RoleEnum
from app.utils.sparkquark_constants import Collection


async def seed_system_roles(db: AsyncIOMotorDatabase, org_id: str) -> None:
    """Seed system roles with their permissions"""

    # Admin: Full access
    admin_permissions = [perm.value for perm in PermissionEnum]

    # Manager: Can manage members, conversations, teams
    manager_permissions = [
        "CONVERSATION_READ",
        "CONVERSATION_UPDATE",
        "CONVERSATION_ASSIGN",
        "CONVERSATION_CLOSE",
        "MESSAGE_READ",
        "MESSAGE_SEND",
        "MESSAGE_EDIT",
        "MEMBER_READ",
        "MEMBER_INVITE",
        "MEMBER_UPDATE",
        "TEAM_READ",
        "TEAM_UPDATE",
        "INTEGRATION_READ",
    ]

    # Agent: Can handle conversations and send messages
    agent_permissions = [
        "CONVERSATION_READ",
        "CONVERSATION_UPDATE",
        "MESSAGE_READ",
        "MESSAGE_SEND",
        "MESSAGE_EDIT",
        "MEMBER_READ",
        "INTEGRATION_READ",
    ]

    # Viewer: Read-only access
    viewer_permissions = [
        "CONVERSATION_READ",
        "MESSAGE_READ",
        "MEMBER_READ",
        "TEAM_READ",
        "INTEGRATION_READ",
    ]

    roles_data = [
        {
            "organization_id": org_id,
            "name": "Admin",
            "description": "Full system access",
            "permissions": admin_permissions,
            "is_system_role": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "organization_id": org_id,
            "name": "Manager",
            "description": "Manage team and conversations",
            "permissions": manager_permissions,
            "is_system_role": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "organization_id": org_id,
            "name": "Agent",
            "description": "Handle customer conversations",
            "permissions": agent_permissions,
            "is_system_role": True,
            "created_at": datetime.now(timezone.utc),
        },
        {
            "organization_id": org_id,
            "name": "Viewer",
            "description": "Read-only access",
            "permissions": viewer_permissions,
            "is_system_role": True,
            "created_at": datetime.now(timezone.utc),
        },
    ]

    roles_collection = db[Collection.ROLES]

    for role_data in roles_data:
        # Check if role already exists
        existing = await roles_collection.find_one({
            "organization_id": org_id,
            "name": role_data["name"],
        })

        if not existing:
            await roles_collection.insert_one(role_data)


async def seed_all(db: AsyncIOMotorDatabase, org_id: str) -> None:
    """Run all seeders"""
    await seed_system_roles(db, org_id)


async def clear_seeds(db: AsyncIOMotorDatabase, org_id: str) -> None:
    """Clear seeded data (system roles only)"""
    await db[Collection.ROLES].delete_many({
        "organization_id": org_id,
        "is_system_role": True,
    })
