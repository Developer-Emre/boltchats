import secrets
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    NotFoundException,
    ForbiddenException,
    ConflictException,
)
from app.schemas.invitation_schema import (
    CreateInvitationRequest,
    InvitationResponse,
    InvitationListResponse,
)
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 20
_MAX_LIMIT: int = 100
_INVITATION_EXPIRY_DAYS: int = 7


def _doc_to_invitation(doc: dict) -> InvitationResponse:
    return InvitationResponse(
        id=str(doc["_id"]),
        workspace_id=doc["workspace_id"],
        invited_email=doc["invited_email"],
        role=doc.get("role", "member"),
        code=doc["code"],
        status=doc.get("status", "pending"),
        invited_by=doc["invited_by"],
        created_at=doc["created_at"],
        expires_at=doc.get("expires_at"),
        updated_at=doc["updated_at"],
    )


def _generate_invitation_code() -> str:
    """Generate a unique invitation code."""
    return secrets.token_urlsafe(16)


async def create(
    workspace_id: str,
    payload: CreateInvitationRequest,
    inviter_id: str,
    db,
) -> InvitationResponse:
    """Create an invitation to workspace."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=_INVITATION_EXPIRY_DAYS)
    code = _generate_invitation_code()

    doc = {
        "workspace_id": workspace_id,
        "invited_email": payload.email,
        "role": payload.role,
        "code": code,
        "status": "pending",
        "invited_by": inviter_id,
        "created_at": now,
        "expires_at": expires_at,
        "updated_at": now,
    }

    try:
        result = await db[Collection.INVITATIONS].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create invitation") from exc

    doc["_id"] = result.inserted_id
    await logger.ainfo(
        "invitation_created",
        invitation_id=str(result.inserted_id),
        workspace_id=workspace_id,
        invited_email=payload.email,
        invited_by=inviter_id,
    )

    return _doc_to_invitation(doc)


async def get_by_code(code: str, db) -> InvitationResponse:
    """Get invitation by code."""
    try:
        doc = await db[Collection.INVITATIONS].find_one({"code": code})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query invitation") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    # Check if expired
    if doc["expires_at"] < datetime.now(timezone.utc):
        raise NotFoundException(ErrorMessage.INVITATION_EXPIRED)

    # Check if already accepted
    if doc["status"] != "pending":
        raise ConflictException(f"Invitation already {doc['status']}")

    return _doc_to_invitation(doc)


async def list_by_workspace(
    workspace_id: str,
    db,
    cursor: str | None = None,
    limit: int = _DEFAULT_LIMIT,
) -> InvitationListResponse:
    """List all pending invitations for workspace."""
    limit = min(limit, _MAX_LIMIT)
    query: dict = {"workspace_id": workspace_id, "status": "pending"}

    if cursor:
        cursor_oid = parse_object_id(cursor, ErrorMessage.INVALID_ID)
        query["_id"] = {"$gt": cursor_oid}

    try:
        docs = (
            await db[Collection.INVITATIONS]
            .find(query)
            .sort("_id", 1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to list invitations") from exc

    has_more = len(docs) > limit
    items = [_doc_to_invitation(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None

    return InvitationListResponse(items=items, next_cursor=next_cursor)


async def accept(code: str, user_id: str, db) -> InvitationResponse:
    """Accept an invitation and add user to workspace."""
    now = datetime.now(timezone.utc)

    try:
        invitation = await db[Collection.INVITATIONS].find_one_and_update(
            {"code": code, "status": "pending"},
            {
                "$set": {
                    "status": "accepted",
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to accept invitation") from exc

    if not invitation:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    # Check if expired
    if invitation["expires_at"] < now:
        raise NotFoundException(ErrorMessage.INVITATION_EXPIRED)

    workspace_id = invitation["workspace_id"]

    # Add user to workspace
    try:
        await db[Collection.WORKSPACES].find_one_and_update(
            {
                "_id": ObjectId(workspace_id),
                "members.user_id": {"$ne": user_id},
            },
            {
                "$push": {
                    "members": {
                        "user_id": user_id,
                        "role": invitation.get("role", "member"),
                        "joined_at": now,
                        "is_active": True,
                    }
                },
                "$inc": {"member_count": 1},
                "$set": {"updated_at": now},
            },
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to add user to workspace") from exc

    # Add workspace to user's workspaces
    try:
        await db[Collection.USERS].update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {
                    "workspaces": {
                        "workspace_id": workspace_id,
                        "role": invitation.get("role", "member"),
                        "joined_at": now,
                        "is_active": True,
                    }
                }
            },
        )
    except PyMongoError as exc:
        await logger.aerror("Failed to update user workspaces", exc_info=True)

    await logger.ainfo(
        "invitation_accepted",
        invitation_code=code,
        workspace_id=workspace_id,
        user_id=user_id,
    )

    return _doc_to_invitation(invitation)


async def revoke(invitation_id: str, user_id: str, db) -> InvitationResponse:
    """Revoke an invitation (admin/owner only)."""
    oid = parse_object_id(invitation_id, ErrorMessage.INVITATION_NOT_FOUND)

    # Get invitation to check workspace
    try:
        invitation = await db[Collection.INVITATIONS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query invitation") from exc

    if not invitation:
        raise NotFoundException(ErrorMessage.INVITATION_NOT_FOUND)

    # TODO: Verify user is admin/owner of workspace

    try:
        updated = await db[Collection.INVITATIONS].find_one_and_update(
            {"_id": oid},
            {
                "$set": {
                    "status": "revoked",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to revoke invitation") from exc

    await logger.ainfo(
        "invitation_revoked",
        invitation_id=invitation_id,
        workspace_id=invitation["workspace_id"],
        revoked_by=user_id,
    )

    return _doc_to_invitation(updated)
