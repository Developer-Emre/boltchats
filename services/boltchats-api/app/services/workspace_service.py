from datetime import datetime, timezone
from bson.objectid import ObjectId

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.schemas.workspace_schema import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    WorkspaceResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    WorkspaceMemberSchema,
)
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id, generate_slug

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 20
_MAX_LIMIT: int = 100


def _doc_to_workspace(doc: dict) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        slug=doc["slug"],
        description=doc.get("description", ""),
        icon_url=doc.get("icon_url"),
        owner_id=doc["owner_id"],
        member_count=doc.get("member_count", 0),
        channel_count=doc.get("channel_count", 0),
        message_count=doc.get("message_count", 0),
        is_active=doc.get("is_active", True),
        is_archived=doc.get("is_archived", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _doc_to_workspace_detail(doc: dict) -> WorkspaceDetailResponse:
    members = [
        WorkspaceMemberSchema(
            user_id=m["user_id"],
            role=m["role"],
            joined_at=m["joined_at"],
            is_active=m.get("is_active", True),
        )
        for m in doc.get("members", [])
    ]
    return WorkspaceDetailResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        slug=doc["slug"],
        description=doc.get("description", ""),
        icon_url=doc.get("icon_url"),
        owner_id=doc["owner_id"],
        members=members,
        settings=doc.get("settings", {}),
        member_count=doc.get("member_count", 0),
        channel_count=doc.get("channel_count", 0),
        message_count=doc.get("message_count", 0),
        is_active=doc.get("is_active", True),
        is_archived=doc.get("is_archived", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def create(
    payload: CreateWorkspaceRequest, owner_id: str, db
) -> WorkspaceResponse:
    """Create a new workspace."""
    now = datetime.now(timezone.utc)
    slug = generate_slug(payload.name)

    # Check if slug already exists
    try:
        existing = await db[Collection.WORKSPACES].find_one({"slug": slug})
        if existing:
            raise ConflictException(f"Workspace with slug '{slug}' already exists")
    except PyMongoError as exc:
        raise DatabaseException("Failed to check workspace slug") from exc

    doc = {
        "name": payload.name,
        "slug": slug,
        "description": payload.description,
        "icon_url": payload.icon_url,
        "owner_id": owner_id,
        "members": [
            {
                "user_id": owner_id,
                "role": "owner",
                "joined_at": now,
                "is_active": True,
            }
        ],
        "settings": {},
        "billing": {"plan": "free"},
        "member_count": 1,
        "channel_count": 0,
        "message_count": 0,
        "is_active": True,
        "is_archived": False,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await db[Collection.WORKSPACES].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create workspace") from exc

    doc["_id"] = result.inserted_id
    await logger.ainfo(
        "workspace_created",
        workspace_id=str(result.inserted_id),
        owner_id=owner_id,
        slug=slug,
    )

    # Add workspace to user's workspaces array
    await db[Collection.USERS].update_one(
        {"_id": ObjectId(owner_id)},
        {
            "$push": {
                "workspaces": {
                    "workspace_id": str(result.inserted_id),
                    "role": "owner",
                    "joined_at": now,
                    "is_active": True,
                }
            }
        },
    )

    return _doc_to_workspace(doc)


async def get_by_id(workspace_id: str, db) -> WorkspaceResponse:
    """Get workspace by ID."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)
    try:
        doc = await db[Collection.WORKSPACES].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query workspace") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.WORKSPACE_NOT_FOUND)

    return _doc_to_workspace(doc)


async def get_detail(workspace_id: str, db) -> WorkspaceDetailResponse:
    """Get workspace with full details including members."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)
    try:
        doc = await db[Collection.WORKSPACES].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query workspace") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.WORKSPACE_NOT_FOUND)

    return _doc_to_workspace_detail(doc)


async def list_by_user(
    user_id: str, db, cursor: str | None = None, limit: int = _DEFAULT_LIMIT
) -> WorkspaceListResponse:
    """List all workspaces for a user."""
    limit = min(limit, _MAX_LIMIT)
    query: dict = {}

    # Match user as member
    query["members.user_id"] = user_id

    if cursor:
        cursor_oid = parse_object_id(cursor, ErrorMessage.INVALID_ID)
        query["_id"] = {"$gt": cursor_oid}

    try:
        docs = (
            await db[Collection.WORKSPACES]
            .find(query)
            .sort("_id", 1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to list workspaces") from exc

    has_more = len(docs) > limit
    items = [_doc_to_workspace(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None

    return WorkspaceListResponse(items=items, next_cursor=next_cursor)


async def update(
    workspace_id: str, payload: UpdateWorkspaceRequest, user_id: str, db
) -> WorkspaceResponse:
    """Update workspace (owner only)."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)

    # Get existing workspace
    try:
        existing = await db[Collection.WORKSPACES].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query workspace") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.WORKSPACE_NOT_FOUND)

    # Check ownership
    if existing["owner_id"] != user_id:
        raise ForbiddenException(ErrorMessage.WORKSPACE_OWNER_ONLY)

    # Build update doc
    update_data = {}
    if payload.name:
        update_data["name"] = payload.name
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.icon_url is not None:
        update_data["icon_url"] = payload.icon_url
    if payload.settings:
        update_data["settings"] = payload.settings.dict()

    update_data["updated_at"] = datetime.now(timezone.utc)

    try:
        doc = await db[Collection.WORKSPACES].find_one_and_update(
            {"_id": oid},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to update workspace") from exc

    await logger.ainfo(
        "workspace_updated", workspace_id=workspace_id, updated_by=user_id
    )
    return _doc_to_workspace(doc)


async def add_member(
    workspace_id: str, new_member_id: str, added_by: str, db
) -> WorkspaceResponse:
    """Add a member to workspace (admin/owner only)."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)

    now = datetime.now(timezone.utc)

    try:
        doc = await db[Collection.WORKSPACES].find_one_and_update(
            {"_id": oid, "members.user_id": {"$ne": new_member_id}},
            {
                "$push": {
                    "members": {
                        "user_id": new_member_id,
                        "role": "member",
                        "joined_at": now,
                        "is_active": True,
                    }
                },
                "$inc": {"member_count": 1},
                "$set": {"updated_at": now},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to add member to workspace") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.WORKSPACE_NOT_FOUND)

    # Add workspace to user's workspaces array
    try:
        await db[Collection.USERS].update_one(
            {"_id": ObjectId(new_member_id)},
            {
                "$push": {
                    "workspaces": {
                        "workspace_id": workspace_id,
                        "role": "member",
                        "joined_at": now,
                        "is_active": True,
                    }
                }
            },
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update user workspaces", exc_info=True)

    await logger.ainfo(
        "workspace_member_added",
        workspace_id=workspace_id,
        member_id=new_member_id,
        added_by=added_by,
    )

    return _doc_to_workspace(doc)


async def remove_member(
    workspace_id: str, member_id: str, removed_by: str, db
) -> WorkspaceResponse:
    """Remove a member from workspace (admin/owner only)."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)

    # Get workspace to check if member is owner
    try:
        workspace = await db[Collection.WORKSPACES].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query workspace") from exc

    if not workspace:
        raise NotFoundException(ErrorMessage.WORKSPACE_NOT_FOUND)

    # Prevent removing owner
    if workspace["owner_id"] == member_id:
        raise ForbiddenException("Cannot remove workspace owner")

    try:
        doc = await db[Collection.WORKSPACES].find_one_and_update(
            {"_id": oid},
            {
                "$pull": {"members": {"user_id": member_id}},
                "$inc": {"member_count": -1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to remove member from workspace") from exc

    # Remove workspace from user's workspaces array
    try:
        await db[Collection.USERS].update_one(
            {"_id": ObjectId(member_id)},
            {"$pull": {"workspaces": {"workspace_id": workspace_id}}},
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update user workspaces", exc_info=True)

    await logger.ainfo(
        "workspace_member_removed",
        workspace_id=workspace_id,
        member_id=member_id,
        removed_by=removed_by,
    )

    return _doc_to_workspace(doc)


async def verify_member_access(
    workspace_id: str, user_id: str, db
) -> WorkspaceResponse:
    """Verify user is member of workspace."""
    oid = parse_object_id(workspace_id, ErrorMessage.WORKSPACE_NOT_FOUND)

    try:
        doc = await db[Collection.WORKSPACES].find_one(
            {"_id": oid, "members.user_id": user_id}
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to query workspace") from exc

    if not doc:
        raise ForbiddenException(ErrorMessage.WORKSPACE_ACCESS_DENIED)

    return _doc_to_workspace(doc)
